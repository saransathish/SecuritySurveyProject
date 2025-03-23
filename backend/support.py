import streamlit as st
import pandas as pd
import os
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.llms import Mistral
from langchain.schema import Document
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain.tools import Tool
import re

# Set up Mistral API key
os.environ["MISTRAL_API_KEY"] = "zoVkipjGVY5dS06jFXYwsRnhl0NyvjpE"  # Replace with your API key

# Initialize Mistral LLM
llm = Mistral(
    model="mistral-medium",  # or any model of your choice
    temperature=0.7,
    streaming=True,
    callbacks=[StreamingStdOutCallbackHandler()]
)

# Function to convert Excel data to documents
def excel_to_documents(excel_file):
    try:
        # Read all sheets from the Excel file
        xl = pd.ExcelFile(excel_file)
        sheet_names = xl.sheet_names
        
        documents = []
        
        for sheet_name in sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            
            # Convert each row to a document
            for idx, row in df.iterrows():
                # Convert row to string and clean it
                content = f"Sheet: {sheet_name}\n"
                for col, value in row.items():
                    if pd.notna(value):  # Check if the value is not NaN
                        content += f"{col}: {value}\n"
                
                # Create document with metadata
                doc = Document(
                    page_content=content,
                    metadata={"source": f"{sheet_name}", "row": idx}
                )
                documents.append(doc)
        
        return documents
    except Exception as e:
        st.error(f"Error processing Excel file: {e}")
        return []

# Function to set up the vector database
def setup_vectordb(documents):
    # Initialize embeddings
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    
    # Split the documents
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    texts = text_splitter.split_documents(documents)
    
    # Create FAISS vector store
    vectorstore = FAISS.from_documents(texts, embeddings)
    
    return vectorstore

# Custom tool for security survey responses
def security_survey_tool(query):
    """Tool to query the security survey database for relevant information."""
    # This would typically be more complex, but for demonstration,
    # we'll use the retriever directly
    docs = retriever.get_relevant_documents(query)
    if docs:
        return "\n\n".join([doc.page_content for doc in docs[:3]])
    return "No relevant information found."

# Custom tool for risk mitigation recommendations
def risk_mitigation_tool(risk_type):
    """Tool to get mitigation strategies for specific security risks."""
    # Creating a more specific query about mitigation strategies
    query = f"What are the mitigation strategies for {risk_type}?"
    docs = retriever.get_relevant_documents(query)
    if docs:
        # Filter for documents that mention mitigation
        mitigation_docs = [doc for doc in docs if "mitigation" in doc.page_content.lower()]
        if mitigation_docs:
            return "\n\n".join([doc.page_content for doc in mitigation_docs[:2]])
    return f"No specific mitigation strategies found for {risk_type}."

# Custom tool for security solutions and costs
def solution_cost_tool(solution_request):
    """Tool to provide information about security solutions and their costs."""
    query = f"What are the solutions and costs for {solution_request}?"
    docs = retriever.get_relevant_documents(query)
    if docs:
        # Filter for documents that mention solutions or costs
        solution_docs = [doc for doc in docs if "solution" in doc.page_content.lower() or "cost" in doc.page_content.lower()]
        if solution_docs:
            return "\n\n".join([doc.page_content for doc in solution_docs[:2]])
    return f"No specific solution or cost information found for {solution_request}."

# Streamlit UI
st.title("Security Survey Assessment Chatbot")
st.write("Upload your Security Survey Excel file and ask questions about security risks, mitigations, and solutions.")

# File uploader for Excel file
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "xls"])

# Initialize session state for conversation history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize session state for agent
if "agent" not in st.session_state:
    st.session_state.agent = None

# Process uploaded file
if uploaded_file:
    with st.spinner("Processing Excel data..."):
        # If we don't have documents or a new file is uploaded, process the file
        if "documents" not in st.session_state or st.session_state.uploaded_file_name != uploaded_file.name:
            st.session_state.uploaded_file_name = uploaded_file.name
            documents = excel_to_documents(uploaded_file)
            st.session_state.documents = documents
            
            # Set up vector database
            vectorstore = setup_vectordb(documents)
            st.session_state.vectorstore = vectorstore
            
            # Set up retriever
            retriever = vectorstore.as_retriever(
                search_kwargs={"k": 5}
            )
            st.session_state.retriever = retriever
            
            # Set up tools
            tools = [
                Tool(
                    name="SecuritySurveyTool",
                    func=security_survey_tool,
                    description="Use this tool to get information about security survey questions and risks."
                ),
                Tool(
                    name="RiskMitigationTool",
                    func=risk_mitigation_tool,
                    description="Use this tool to get specific mitigation strategies for security risks."
                ),
                Tool(
                    name="SolutionCostTool",
                    func=solution_cost_tool,
                    description="Use this tool to get information about security solutions and their costs."
                )
            ]
            
            # Setup conversation memory
            memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
            
            # Create the agent
            agent = create_structured_chat_agent(llm, tools, "You are a helpful assistant specializing in security survey assessment.")
            agent_executor = AgentExecutor.from_agent_and_tools(
                agent=agent,
                tools=tools,
                memory=memory,
                verbose=True,
                handle_parsing_errors=True
            )
            
            st.session_state.agent = agent_executor
            
            st.success("Excel data processed successfully!")
    
    # Display chat interface
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask a question about security survey assessment"):
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Get the agent response
                    retriever = st.session_state.retriever
                    response = st.session_state.agent.run(prompt)
                    
                    # Clean up any tool information in the response
                    cleaned_response = re.sub(r'Action: .*?\n', '', response)
                    cleaned_response = re.sub(r'Action Input: .*?\n', '', cleaned_response)
                    cleaned_response = re.sub(r'Observation: .*?\n', '', cleaned_response)
                    cleaned_response = cleaned_response.strip()
                    
                    st.markdown(cleaned_response)
                    
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": cleaned_response})
                except Exception as e:
                    error_message = f"Error generating response: {str(e)}"
                    st.error(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": error_message})
else:
    st.info("Please upload your security survey Excel file to get started.")

# Simple explanation of capabilities
st.sidebar.title("Chatbot Information")
st.sidebar.markdown("""
## How to use this chatbot
1. Upload your security survey Excel file
2. Ask questions about:
   - Security risks and vulnerabilities
   - Mitigation strategies
   - Security solutions and costs
   - Survey assessment responses

## Example Questions
- What are the common physical security risks?
- How can we mitigate violence risks?
- What solutions are available for theft prevention?
- How much does CCTV implementation cost?
- What are the best practices for access control?
""")