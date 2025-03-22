from flask import Flask, request, jsonify, send_file
from fpdf.enums import XPos, YPos
from flask_cors import CORS
import pandas as pd
import json
from datetime import datetime
import os
import base64
from fpdf import FPDF
from typing import Dict, List, Any, Optional
from langchain_mistralai.chat_models import ChatMistralAI
from langchain.memory import ConversationBufferMemory
from langchain.tools import BaseTool
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from pydantic import Field
import uuid
from dotenv import load_dotenv
import googlemaps
import requests
from geopy.geocoders import Nominatim
import time
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
load_dotenv()

app = Flask(__name__)
CORS(app)

# Load the API key from environment variables
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

# Define tools and data processor
class RiskAnalyzerTool(BaseTool):
    name: str = "risk_analyzer"
    description: str = "Analyzes security risks based on survey responses"
    data_processor: Any = Field(default=None)
    
    def _run(self, answers: str) -> List[str]:
        answers_dict = json.loads(answers)
        return self.data_processor.analyze_risks(answers_dict)
    
    async def _arun(self, answers: str) -> List[str]:
        raise NotImplementedError("Async not implemented")

class MitigationTool(BaseTool):
    name: str = "mitigation_finder"
    description: str = "Finds comprehensive mitigation steps for identified risks"
    data_processor: Any = Field(default=None)
    
    def _run(self, risk_type: str) -> Dict:
        return self.data_processor.get_mitigation_steps(risk_type)
    
    async def _arun(self, risk_type: str) -> Dict:
        raise NotImplementedError("Async not implemented")

class AssuranceMetricsTool(BaseTool):
    name: str = "assurance_metrics"
    description: str = "Gets detailed assurance metrics for security solutions"
    data_processor: Any = Field(default=None)
    
    def _run(self, solution: str) -> Dict:
        return self.data_processor.get_solution_details(solution)
    
    async def _arun(self, solution: str) -> Dict:
        raise NotImplementedError("Async not implemented")

class DataProcessor:
    def __init__(self):
        try:
            self.survey_data = pd.read_excel("assumption.xlsx", sheet_name="Survey Questions")
            self.risk_matrix = pd.read_excel("assumption.xlsx", sheet_name="Risk > Mitigation Matrix")
            self.assurance_matrix = pd.read_excel("assumption.xlsx", sheet_name="Assurance Metrics")
        except Exception as e:
            print(f"Error loading Excel file: {str(e)}")
            raise

    def analyze_risks(self, answers: Dict[str, str]) -> List[str]:
        identified_risks = set()
        for question, answer in answers.items():
            if answer.lower() in ['no', 'n']:
                question_data = self.survey_data[
                    self.survey_data['Question'] == question
                ]
                if not question_data.empty and pd.notna(question_data.iloc[0]['Risk Present']):
                    risks = question_data.iloc[0]['Risk Present'].split(',')
                    identified_risks.update([risk.strip() for risk in risks])
        return list(identified_risks)

    def get_mitigation_steps(self, risk_type: str) -> Dict[str, Any]:
        try:
            risk_data = self.risk_matrix[self.risk_matrix['Risk Type'].str.strip() == risk_type.strip()]
            
            if risk_data.empty:
                # Skip warning and return empty mitigations
                return {
                    'mitigations': {
                        'tech': [], 'human': [], 'tss': [], 
                        'analytics': [], 'policy': []
                    },
                    'solution_details': {}
                }
            
            risk_row = risk_data.iloc[0]
            
            mitigations = {
                'tech': [x.strip() for x in str(risk_row['Tech Mitigation']).split(',')] if pd.notna(risk_row['Tech Mitigation']) else [],
                'human': [x.strip() for x in str(risk_row['Human Mitigation']).split(',')] if pd.notna(risk_row['Human Mitigation']) else [],
                'tss': [x.strip() for x in str(risk_row['TSS Mitigation']).split(',')] if pd.notna(risk_row['TSS Mitigation']) else [],
                'analytics': [x.strip() for x in str(risk_row['Analytics Mitigation']).split(',')] if pd.notna(risk_row['Analytics Mitigation']) else [],
                'policy': [x.strip() for x in str(risk_row['Policy Mitigation']).split(',')] if pd.notna(risk_row['Policy Mitigation']) else []
            }
            
            for key in mitigations:
                mitigations[key] = [item for item in mitigations[key] if item and item != 'nan']
            
            solution_details = {}
            all_mitigations = []
            for mitigation_list in mitigations.values():
                all_mitigations.extend(mitigation_list)
            
            for mitigation in all_mitigations:
                solution_data = self.get_solution_details(mitigation)
                if solution_data:
                    solution_details[mitigation] = solution_data
            
            return {
                'mitigations': mitigations,
                'solution_details': solution_details
            }
            
        except Exception as e:
            print(f"Error getting mitigation steps: {str(e)}")
            return {
                'mitigations': {
                    'tech': [], 'human': [], 'tss': [], 
                    'analytics': [], 'policy': []
                },
                'solution_details': {}
            }
        
    def get_solution_details(self, solution_name: str) -> Dict[str, Any]:
        try:
            solution_data = self.assurance_matrix[
                self.assurance_matrix['Solution'] == solution_name
            ]
            
            if solution_data.empty:
                return None
                
            data = solution_data.iloc[0]
            return {
                'use_case': data['Use case'] if pd.notna(data['Use case']) else "",
                'links': data['Links to use case'] if pd.notna(data['Links to use case']) else "",
                'partners': data['Partner(s)'] if pd.notna(data['Partner(s)']) else "",
                'data_format': data['Data Format'] if pd.notna(data['Data Format']) else "",
                'immediate_actions': [x.strip() for x in str(data['Data type (Immediate Action)']).split(',')] if pd.notna(data['Data type (Immediate Action)']) else [],
                'data_collation': [x.strip() for x in str(data['Data type (Data Collation)']).split(',')] if pd.notna(data['Data type (Data Collation)']) else [],
                'dashboard': [x.strip() for x in str(data['Eco System outputs/results - Dashboard']).split(',')] if pd.notna(data['Eco System outputs/results - Dashboard']) else [],
                'wearable': [x.strip() for x in str(data['Eco System outputs/results - Wearable']).split(',')] if pd.notna(data['Eco System outputs/results - Wearable']) else [],
                'mobile': [x.strip() for x in str(data['Eco System outputs/results - Mobile']).split(',')] if pd.notna(data['Eco System outputs/results - Mobile']) else [],
                'soc': [x.strip() for x in str(data['Eco System outputs/results - SOC']).split(',')] if pd.notna(data['Eco System outputs/results - SOC']) else [],
                'audio_visual': [x.strip() for x in str(data['Eco System outputs/results - Audio/Visual']).split(',')] if pd.notna(data['Eco System outputs/results - Audio/Visual']) else []
            }
        except Exception as e:
            print(f"Error getting solution details: {str(e)}")
            return None

# Add this class after the DataProcessor class
class AreaAnalysis:
    def __init__(self):
        # Load API key from environment variables
        self.google_api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        self.gmaps = googlemaps.Client(key=self.google_api_key) if self.google_api_key else None
        self.geolocator = Nominatim(user_agent="security_assessment_app")
        
    def geocode_address(self, address, postcode):
        """Convert address to latitude and longitude"""
        try:
            # Combine address and postcode for better results
            full_address = f"{address}, {postcode}"
            location = self.geolocator.geocode(full_address)
            
            if location:
                return {
                    'lat': location.latitude,
                    'lng': location.longitude,
                    'formatted_address': location.address
                }
            else:
                # Try just with postcode if full address fails
                location = self.geolocator.geocode(postcode)
                if location:
                    return {
                        'lat': location.latitude,
                        'lng': location.longitude,
                        'formatted_address': location.address
                    }
                else:
                    return None
        except Exception as e:
            print(f"Geocoding error: {str(e)}")
            return None
    
    def find_nearby_places(self, location, place_type, radius=8000, keyword=None):
        """Find places of a specific type within radius (in meters)"""
        if not self.gmaps:
            return []
            
        try:
            places_result = []
            params = {
                'location': (location['lat'], location['lng']),
                'radius': radius,
                'type': place_type
            }
            
            if keyword:
                params['keyword'] = keyword
                
            places = self.gmaps.places_nearby(**params)
            
            if 'results' in places:
                places_result.extend(places['results'])
                
            # Handle pagination if there are more results
            while 'next_page_token' in places:
                # Need to wait before requesting next page
                time.sleep(2)
                next_page_token = places['next_page_token']
                places = self.gmaps.places_nearby(
                    page_token=next_page_token
                )
                if 'results' in places:
                    places_result.extend(places['results'])
            
            return places_result
        except Exception as e:
            print(f"Error finding nearby places: {str(e)}")
            return []
    
    def get_population_density(self, postcode):
        """Estimate population density based on available data"""
        # This would ideally use a demographic API
        # For now, return a placeholder value or use a free API if available
        try:
            # Placeholder for actual API call
            return {
                'density': 'Medium',  # Low/Medium/High placeholder
                'estimated_population': '5,000-10,000 within 1 mile radius'  # Placeholder
            }
        except Exception as e:
            print(f"Error getting population density: {str(e)}")
            return {
                'density': 'Unknown',
                'estimated_population': 'Data not available'
            }
    
    def analyze_area(self, address, postcode):
        """Perform comprehensive area analysis"""
        location = self.geocode_address(address, postcode)
        
        if not location:
            return {
                'success': False,
                'error': 'Could not geocode the address'
            }
            
        results = {
            'success': True,
            'location': location,
            'schools': [],
            'retail_areas': [],
            'transport': {
                'bus_stations': [],
                'train_stations': []
            },
            'major_junctions': [],
            'population': {}
        }
        
        # Find nearby schools
        schools = self.find_nearby_places(location, 'school')
        results['schools'] = [{
            'name': school.get('name', 'Unnamed School'),
            'vicinity': school.get('vicinity', 'Unknown location'),
            'rating': school.get('rating', 'Not rated'),
            'types': school.get('types', [])
        } for school in schools[:10]]  # Limit to 10 schools
        
        # Find retail areas (shopping_mall, department_store)
        retail_areas = (
            self.find_nearby_places(location, 'shopping_mall') + 
            self.find_nearby_places(location, 'department_store') +
            self.find_nearby_places(location, 'store', keyword='retail')
        )
        results['retail_areas'] = [{
            'name': retail.get('name', 'Unnamed Retail'),
            'vicinity': retail.get('vicinity', 'Unknown location'),
            'rating': retail.get('rating', 'Not rated'),
            'types': retail.get('types', [])
        } for retail in retail_areas[:10]]  # Limit to 10 retail areas
        
        # Find transport hubs
        bus_stations = self.find_nearby_places(location, 'bus_station')
        train_stations = self.find_nearby_places(location, 'train_station')
        
        results['transport']['bus_stations'] = [{
            'name': station.get('name', 'Unnamed Station'),
            'vicinity': station.get('vicinity', 'Unknown location')
        } for station in bus_stations[:5]]  # Limit to 5 stations
        
        results['transport']['train_stations'] = [{
            'name': station.get('name', 'Unnamed Station'),
            'vicinity': station.get('vicinity', 'Unknown location')
        } for station in train_stations[:5]]  # Limit to 5 stations
        
        # Find major roads/junctions
        # Using a keyword search for major intersections
        junctions = self.find_nearby_places(location, 'intersection', keyword='junction')
        results['major_junctions'] = [{
            'name': junction.get('name', 'Unnamed Junction'),
            'vicinity': junction.get('vicinity', 'Unknown location')
        } for junction in junctions[:5]]  # Limit to 5 junctions
        
        # Get population data
        results['population'] = self.get_population_density(postcode)
        
        # Count student population based on schools and their types
        university_count = sum(1 for school in schools if 'university' in school.get('types', []))
        college_count = sum(1 for school in schools if 'school' in school.get('types', []) and 'university' not in school.get('types', []))
        
        # Estimate student population
        results['student_population'] = {
            'universities': university_count,
            'colleges': college_count,
            'estimated_students': 'High' if university_count > 0 else ('Medium' if college_count > 3 else 'Low')
        }
        
        return results
    
# Store Information class
class StoreInformation:
    def __init__(self):
        self.store_fields = [
            {"field": "Store Name", "question": "What is your store name?"},
            {"field": "Store Identifier", "question": "What is your store identifier?"},
            {"field": "Address", "question": "What is the store address?"},
            {"field": "Postcode", "question": "What is the store postcode?"},
            # {"field": "Store Format", "question": "What format is the store? (Superstore/Convenience store/Department store)"},
            # {"field": "Location Footprint", "question": "What is the store's location footprint? (Retail park/Shopping centre/High street)"},
            # {"field": "Selling Area Percentage", "question": "What percentage of the store size is selling area?"},
            # {"field": "Service Checkout Counters", "question": "How many serviced checkout counters are available?"},
            # {"field": "Self Service Checkouts", "question": "Do you have self service checkouts? (Yes/No)"},
            # {"field": "High Risk Assets", "question": "What high-risk or high-value assets are present?"},
            # {"field": "ATM Present", "question": "Do you have an ATM? (Yes/No)"},
            # {"field": "ATM Type", "question": "What type of ATM do you have? (None/Freestanding/TTW/Both)"},
            # {"field": "Customer Toilet", "question": "Do you have a customer toilet? (Yes/No)"},
            # {"field": "Fitting Rooms", "question": "Do you have fitting rooms? (Yes/No)"}
        ]
        self.store_data = {}
        self.current_field_idx = 0

    def get_next_question(self):
        if self.current_field_idx < len(self.store_fields):
            return self.store_fields[self.current_field_idx]
        return None

    def process_answer(self, answer):
        current_field = self.store_fields[self.current_field_idx]
        self.store_data[current_field["field"]] = answer
        self.current_field_idx += 1

    def is_complete(self):
        return self.current_field_idx >= len(self.store_fields)

# PDF Report Generator
class PDFReport:
    def __init__(self):
        self.elements = []
        self.styles = getSampleStyleSheet()
        
        # Add custom styles
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            alignment=1,  # Center
            textColor=colors.darkblue
        ))
        
        self.styles.add(ParagraphStyle(
            name='Section',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.black
        ))
        
        self.styles.add(ParagraphStyle(
            name='Content',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.black
        ))
    
    def add_title(self, title):
        self.elements.append(Paragraph(title, self.styles['CustomTitle']))
        self.elements.append(Spacer(1, 12))
    
    def add_section(self, title):
        self.elements.append(Paragraph(title, self.styles['Section']))
        self.elements.append(Spacer(1, 6))
    
    def add_content(self, content):
        self.elements.append(Paragraph(content, self.styles['Content']))
        self.elements.append(Spacer(1, 3))
    
    def add_store_info(self, store_data):
        self.add_section("Store Information")
        for field, value in store_data.items():
            self.add_content(f"<b>{field}:</b> {value}")
    
    def add_survey_responses(self, answers):
        self.add_section("Survey Responses")
        for question, answer in answers.items():
            self.add_content(f"<b>Q:</b> {question}")
            self.add_content(f"<b>A:</b> {answer}")
            self.elements.append(Spacer(1, 3))
    
    def add_quick_report(self, report, store_data, answers):
        self.add_store_info(store_data)
        self.add_survey_responses(answers)
        
        self.add_section("Quick Analysis Summary")
        self.add_content(report['risk_summary'])
        
        self.add_section("Identified Risks")
        risks_text = ", ".join(report['identified_risks'])
        self.add_content(risks_text)
        
        self.add_section("Available Solutions")
        solutions_text = ", ".join(report['unique_solutions'])
        self.add_content(solutions_text)
    
    def add_detailed_report(self, report, store_data, answers):
        self.add_store_info(store_data)
        self.add_survey_responses(answers)
        
        for risk_data in report['identified_risks']:
            self.add_section(f"Risk: {risk_data['risk_type']}")
            
            mitigations = risk_data['mitigations']['mitigations']
            solution_details = risk_data['mitigations']['solution_details']
            
            # Add Mitigations
            self.add_section("Mitigation Steps")
            for category, items in mitigations.items():
                if items:
                    category_text = f"<b>{category.title()}:</b> {', '.join(items)}"
                    self.add_content(category_text)
            
            # Add Implementation Details
            self.add_section("Implementation Details")
            for solution_name, details in solution_details.items():
                if details:
                    self.add_content(f"<b>Solution: {solution_name}</b>")
                    if details['use_case']:
                        self.add_content(f"<b>Use Case:</b> {details['use_case']}")
                    if details['links']:
                        self.add_content(f"<b>Reference Links:</b> {details['links']}")
                    if details['partners']:
                        self.add_content(f"<b>Partners:</b> {details['partners']}")
                    if details['data_format']:
                        self.add_content(f"<b>Data Format:</b> {details['data_format']}")
                    if details['immediate_actions']:
                        self.add_content(f"<b>Immediate Actions:</b> {', '.join(details['immediate_actions'])}")
                    if details['data_collation']:
                        self.add_content(f"<b>Data Collation:</b> {', '.join(details['data_collation'])}")
                    if details['dashboard']:
                        self.add_content(f"<b>Dashboard Features:</b> {', '.join(details['dashboard'])}")
                    if details['wearable']:
                        self.add_content(f"<b>Wearable Features:</b> {', '.join(details['wearable'])}")
                    if details['mobile']:
                        self.add_content(f"<b>Mobile Features:</b> {', '.join(details['mobile'])}")
                    if details['soc']:
                        self.add_content(f"<b>SOC Features:</b> {', '.join(details['soc'])}")
                    if details['audio_visual']:
                        self.add_content(f"<b>Audio/Visual Features:</b> {', '.join(details['audio_visual'])}")
                    self.elements.append(Spacer(1, 6))
                    
    def add_area_analysis_detailed(self, area_data):
        """Add detailed area analysis to the PDF"""
        if not area_data or not area_data.get('success', False):
            self.add_section("Area Analysis")
            self.add_content("Area analysis data not available.")
            return
            
        self.add_section("AREA ANALYSIS")
        
        # Location info
        if 'location' in area_data:
            self.add_content(f"<b>Location:</b> {area_data['location'].get('formatted_address', 'Address not available')}")
            
        # Population info
        if 'population' in area_data:
            self.add_section("Population Demographics")
            pop = area_data['population']
            self.add_content(f"<b>Density:</b> {pop.get('density', 'Unknown')}")
            self.add_content(f"<b>Estimated Population:</b> {pop.get('estimated_population', 'Unknown')}")
            
        # Student population
        if 'student_population' in area_data:
            students = area_data['student_population']
            self.add_content(f"<b>Student Population:</b> {students.get('estimated_students', 'Unknown')}")
            self.add_content(f"<b>Universities nearby:</b> {students.get('universities', 0)}")
            self.add_content(f"<b>Colleges nearby:</b> {students.get('colleges', 0)}")
        
        # Schools
        if 'schools' in area_data and area_data['schools']:
            self.add_section("Educational Institutions Nearby")
            for i, school in enumerate(area_data['schools'][:5], 1):  # Top 5 schools
                self.add_content(f"{i}. <b>{school['name']}</b> - {school['vicinity']}")
                
        # Retail areas
        if 'retail_areas' in area_data and area_data['retail_areas']:
            self.add_section("Retail Areas Nearby")
            for i, retail in enumerate(area_data['retail_areas'][:5], 1):  # Top 5 retail areas
                self.add_content(f"{i}. <b>{retail['name']}</b> - {retail['vicinity']}")
                
        # Transport hubs
        if 'transport' in area_data:
            self.add_section("Transport Infrastructure")
            
            if area_data['transport']['train_stations']:
                self.add_content("<b>Rail Stations:</b>")
                for i, station in enumerate(area_data['transport']['train_stations'], 1):
                    self.add_content(f"{i}. <b>{station['name']}</b> - {station['vicinity']}")
                    
            if area_data['transport']['bus_stations']:
                self.add_content("<b>Bus Stations:</b>")
                for i, station in enumerate(area_data['transport']['bus_stations'], 1):
                    self.add_content(f"{i}. <b>{station['name']}</b> - {station['vicinity']}")
                    
        # Major junctions
        if 'major_junctions' in area_data and area_data['major_junctions']:
            self.add_section("Major Road Junctions")
            for i, junction in enumerate(area_data['major_junctions'], 1):
                self.add_content(f"{i}. <b>{junction['name']}</b> - {junction['vicinity']}")
    
    def add_area_analysis_quick(self, area_data):
        """Add summarized area analysis to the quick PDF report"""
        if not area_data or not area_data.get('success', False):
            self.add_section("Area Analysis")
            self.add_content("Area analysis data not available.")
            return
            
        self.add_section("AREA ANALYSIS SUMMARY")
        
        # Location and Population Summary
        if 'location' in area_data:
            self.add_content(f"<b>Location:</b> {area_data['location'].get('formatted_address', 'Address not available')}")
            
        if 'population' in area_data:
            self.add_content(f"<b>Population Density:</b> {area_data['population'].get('density', 'Unknown')}")
            
        # Count summaries
        school_count = len(area_data.get('schools', []))
        retail_count = len(area_data.get('retail_areas', []))
        bus_count = len(area_data.get('transport', {}).get('bus_stations', []))
        train_count = len(area_data.get('transport', {}).get('train_stations', []))
        
        self.add_content("<b>Nearby Points of Interest:</b>")
        self.add_content(f"• <b>Schools:</b> {school_count}")
        self.add_content(f"• <b>Retail Areas:</b> {retail_count}")
        self.add_content(f"• <b>Train Stations:</b> {train_count}")
        self.add_content(f"• <b>Bus Stations:</b> {bus_count}")
        
        if 'student_population' in area_data:
            self.add_content(f"• <b>Student Population:</b> {area_data['student_population'].get('estimated_students', 'Unknown')}")
    
    def generate_pdf(self, filename):
        """Generate PDF file with the given filename"""
        try:
            doc = SimpleDocTemplate(filename, pagesize=letter)
            doc.build(self.elements)
            return True
        except Exception as e:
            print(f"Error generating PDF: {str(e)}")
            return False
        
# Risk Assessment Chat class
class RiskAssessmentChat:
    def __init__(self, session_id=None):
        self.session_id = session_id or str(uuid.uuid4())
        self.data_processor = DataProcessor()
        self.llm = ChatMistralAI(
            mistral_api_key=MISTRAL_API_KEY,
            model="mistral-large")
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        self.current_question_idx = 0
        self.answers = {}
        self.store_info = StoreInformation()
        self.setup_tools()
        self.setup_agent()
        self.state = "store_info"
        self.messages = []
        self.area_analysis = AreaAnalysis()
        self.area_data = None

    def setup_tools(self):
        self.risk_analyzer = RiskAnalyzerTool(data_processor=self.data_processor)
        self.mitigation_tool = MitigationTool(data_processor=self.data_processor)
        self.assurance_tool = AssuranceMetricsTool(data_processor=self.data_processor)
        
        self.tools = [self.risk_analyzer, self.mitigation_tool, self.assurance_tool]

    def setup_agent(self):
        prompt = PromptTemplate.from_template(
            """You are a security risk assessment expert. Use the available tools to analyze risks 
            and provide recommendations.

            Current conversation:
            {chat_history}

            Human: {input}
            Assistant: Let me help you with that analysis.

            Available Tools:
            {tools}

            {agent_scratchpad}

            Tool Names: {tool_names}
            """
        )

        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )

        self.agent_executor = AgentExecutor.from_agent_and_tools(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True
        )

    def get_next_question(self):
        if self.current_question_idx < len(self.data_processor.survey_data):
            return self.data_processor.survey_data.iloc[self.current_question_idx]['Question']
        return None

    def process_answer(self, answer):
        question = self.data_processor.survey_data.iloc[self.current_question_idx]['Question']
        self.answers[question] = answer
        self.current_question_idx += 1

    def generate_quick_report(self):
        risks = self.data_processor.analyze_risks(self.answers)
        unique_solutions = set()
        unique_risks = set()
        
        report = {
            'identified_risks': [],
            'unique_solutions': [],
            'risk_summary': ''
        }
        
        for risk in risks:
            unique_risks.add(risk)
            risk_data = self.data_processor.get_mitigation_steps(risk)
            for category in risk_data['mitigations'].values():
                unique_solutions.update(category)
        
        report['identified_risks'] = list(unique_risks)
        report['unique_solutions'] = list(unique_solutions)
        report['risk_summary'] = f"Analysis identified {len(unique_risks)} risks with {len(unique_solutions)} possible solutions."
        
        return report

    def generate_detailed_report(self):
        risks = self.data_processor.analyze_risks(self.answers)
        report = {
            'identified_risks': []
        }

        for risk in risks:
            risk_data = {
                'risk_type': risk,
                'mitigations': self.data_processor.get_mitigation_steps(risk)
            }
            report['identified_risks'].append(risk_data)

        return report
    
    def perform_area_analysis(self):
        """Perform area analysis based on store information"""
        if not self.store_info.store_data:
            return None
            
        address = self.store_info.store_data.get('Address', '')
        postcode = self.store_info.store_data.get('Postcode', '')
        
        if not address or not postcode:
            return None
            
        self.area_data = self.area_analysis.analyze_area(address, postcode)
        return self.area_data
    
    def generate_pdf_report(self, report_type="detailed"):
        if report_type == "detailed":
            report = self.generate_detailed_report()
        else:
            report = self.generate_quick_report()
            
        # Perform area analysis if not already done
        if not self.area_data:
            self.perform_area_analysis()
            
        pdf_generator = PDFReport()
        pdf_generator.add_title("Security Risk Assessment Report")
        pdf_generator.add_content(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if report_type == "detailed":
            if self.area_data:
                pdf_generator.add_area_analysis_detailed(self.area_data)
            pdf_generator.add_detailed_report(report, self.store_info.store_data, self.answers)
        else:
            if self.area_data:
                pdf_generator.add_area_analysis_quick(self.area_data)
            pdf_generator.add_quick_report(report, self.store_info.store_data, self.answers)
            
        
        filename = f"security_assessment_{report_type}_{self.session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        if pdf_generator.generate_pdf(filename):
            return filename
        return None
    
# Session storage
sessions = {}

# Helper function to get or create session
def get_session(session_id=None):
    if session_id and session_id in sessions:
        return sessions[session_id]
    
    # Create new session
    new_session = RiskAssessmentChat(session_id)
    session_id = new_session.session_id
    sessions[session_id] = new_session
    return new_session

@app.route('/api/start_session', methods=['POST'])
def start_session():
    session = get_session()
    return jsonify({
        'session_id': session.session_id,
        'state': session.state,
        'message': "Welcome to the Security Risk Assessment. Let's start by collecting some information about your store."
    })

@app.route('/api/message', methods=['POST'])
def handle_message():
    data = request.json
    session_id = data.get('session_id')
    user_message = data.get('message')
    
    if not session_id or not user_message:
        return jsonify({'error': 'Missing session_id or message'}), 400
    
    session = get_session(session_id)
    
    # Process message based on the current state
    if session.state == "store_info":
        field_info = session.store_info.get_next_question()
        
        if field_info:
            session.store_info.process_answer(user_message)
            
            if session.store_info.is_complete():
                session.state = "survey"
                next_question = session.get_next_question()
                return jsonify({
                    'session_id': session_id,
                    'state': session.state,
                    'message': f"Store information complete. Now let's begin the survey.\n\n**Survey Question**: {next_question}"
                })
            else:
                # Get the next store info question
                next_field = session.store_info.get_next_question()
                return jsonify({
                    'session_id': session_id,
                    'state': session.state,
                    'message': next_field['question']
                })
        
    elif session.state == "survey":
        question = session.get_next_question()
        
        if question:
            # Validate Y/N answer
            if user_message.upper() not in ['Y', 'N', 'YES', 'NO']:
                return jsonify({
                    'session_id': session_id,
                    'state': session.state,
                    'message': "Please answer with Y or N",
                    'error': True
                })
            
            session.process_answer(user_message)
            next_question = session.get_next_question()
            
            if next_question:
                return jsonify({
                    'session_id': session_id,
                    'state': session.state,
                    'message': f"**Survey Question**: {next_question}"
                })
            else:
                session.state = "report"
                return jsonify({
                    'session_id': session_id,
                    'state': session.state,
                    'message': "Survey complete! Generating analysis..."
                })
        
    elif session.state == "report":
        # This handles any messages after the report is complete
        return jsonify({
            'session_id': session_id,
            'state': session.state,
            'message': "Your security assessment is complete. You can download the reports using the links provided."
        })
    
    # Default response if none of the conditions are met
    return jsonify({
        'session_id': session_id,
        'state': session.state,
        'message': "I didn't understand that. Please try again."
    })

# Update the get_report_status endpoint
@app.route('/api/get_report', methods=['GET'])
def get_report_status():
    session_id = request.args.get('session_id')
    
    if not session_id or session_id not in sessions:
        return jsonify({'error': 'Invalid session_id'}), 400
    
    session = sessions[session_id]
    
    if session.state != "report":
        return jsonify({
            'ready': False,
            'message': "The survey is not yet complete."
        })
    
    # Generate the reports data
    quick_report = session.generate_quick_report()
    detailed_report = session.generate_detailed_report()
    
    # Perform area analysis
    area_data = session.perform_area_analysis()
    
    return jsonify({
        'ready': True,
        'quick_report': quick_report,
        'detailed_report': detailed_report,
        'area_analysis': area_data if area_data and area_data.get('success', False) else None
    })


@app.route('/api/download_report', methods=['GET'])
def download_report():
    session_id = request.args.get('session_id')
    report_type = request.args.get('type', 'detailed')  # 'detailed' or 'quick'
    
    if not session_id or session_id not in sessions:
        return jsonify({'error': 'Invalid session_id'}), 400
    
    session = sessions[session_id]
    
    if session.state != "report":
        return jsonify({'error': 'The survey is not yet complete'}), 400
    
    # Generate the PDF file
    pdf_file = session.generate_pdf_report(report_type)
    
    if not pdf_file or not os.path.exists(pdf_file):
        return jsonify({'error': 'Failed to generate PDF report'}), 500
    
    # Return the file for download
    return send_file(
        pdf_file,
        as_attachment=True,
        download_name=f"security_assessment_{report_type}.pdf"
    )

# Clean up old PDF files (could be implemented as a scheduled task)
@app.route('/api/cleanup', methods=['POST'])
def cleanup_files():
    """Admin endpoint to clean up old PDF files"""
    count = 0
    for file in os.listdir():
        if file.startswith("security_assessment_") and file.endswith(".pdf"):
            file_time = os.path.getmtime(file)
            # Delete files older than 1 hour (3600 seconds)
            if datetime.now().timestamp() - file_time > 3600:
                os.remove(file)
                count += 1
    
    return jsonify({'message': f'Cleaned up {count} old files'})

# Debug status endpoint
@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({
        'status': 'running',
        'active_sessions': len(sessions),
        'session_ids': list(sessions.keys())
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)