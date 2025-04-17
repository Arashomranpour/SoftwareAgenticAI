import os
from dotenv import load_dotenv
import streamlit as st
from dotenv import load_dotenv
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from typing import Annotated, List
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_ollama.chat_models import ChatOllama
import time
from langchain_groq import ChatGroq

load_dotenv()

os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")


class State(TypedDict):
    topic: str
    requirement: str
    coder: str
    tester_res: str
    documenter: str


graph = StateGraph(State)
llm = ChatGroq(model="llama-3.3-70b-versatile")


# def create_node(state, system):
#     """Process messages for each node."""
#     human_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
#     ai_messages = [msg for msg in state["messages"] if isinstance(msg, AIMessage)]
#     sys_messages = [SystemMessage(content=system)]
#     messages = sys_messages + human_messages + ai_messages
#     message = llm.invoke(messages)
#     return {"messages": state["messages"] + [message]}  # Preserve history


# analyst = lambda state: create_node(
#     state,
#     "You are a software requirements analyst. Generate clear requirements for a developer from provided instruction.",
# )
# developer = lambda state: create_node(
#     state,
#     "You are a senior Python developer. Generate advanced, error-free code from provided message.",
#     )
# tester = lambda state: create_node(
#     state,
#     "You are a tester. Check the code for errors and fix if needed. If no errors, confirm as 'developer Good no bugs'.",
# )
# document = lambda state: create_node(
#     state,
#     "You are an expert in technical documentation and summarizing. Summarize technical documentation while retaining all generated source code.",
# )


def analyst(state: State):
    """First LLM call to generate initial code."""
    st.write("📌 analyst called ")
    msg = llm.invoke(
        [
            SystemMessage(
                content="You are a software requirements analyst. Generate clear requirements for a developer from provided instruction"
            ),
            HumanMessage(
                content=f"Write a simple and professinal software requirements about {state['topic']}"
            ),
        ]
    )
    st.markdown(msg.content)

    return {"requirement": msg.content}


def developer(state: State):
    st.write("👨‍💻 developer called")
    msg = llm.invoke(
        [
            SystemMessage(
                content="You are senior fullstack developer. Generate advanced, error-free code from provided requirement list"
            ),
            HumanMessage(
                content=f"Write a professinal code about {state['requirement']} and the topic is {state["topic"]}"
            ),
        ]
    )
    st.markdown(msg.content)
    return {"coder": msg.content}


def tester(state: State):
    st.write("🛠 tester called")

    msg = llm.invoke(
        [
            SystemMessage(
                content=f"You are an expert software devloper and tester. Check the code for errors or any implemention needed based on {state["requirement"]} if there was any error or Implementation required based on the requirements or any empty functions only return this variable 'shaka' and nothing else  , otherwise pass the whole generated source code"
            ),
            HumanMessage(
                content=f"if any error or Implementation required do as you told else do as you told , here is the code{state['coder']} ,and here is the requirement list that was meant to be developed {state["requirement"]}"
            ),
        ]
    )
    st.markdown(msg.content)

    return {"tester_res": msg.content}


def document(state: State):
    st.write("📄documenter called")

    msg = llm.invoke(
        [
            SystemMessage(
                content="You are an expert in technical documentation and summarizing in software industry. Summarize technical documentation and include generated source code in markdown"
            ),
            HumanMessage(
                content=f"summerize this and give the full code in markdown {state['tester_res']}"
            ),
        ]
    )
    return {"documenter": msg.content}


# Add nodes to the graph
graph.add_node("analyst", analyst)
graph.add_node("developer", developer)
graph.add_node("tester", tester)
graph.add_node("document", document)


def checker(state: State) -> Literal["developer", "document"]:
    """Conditional routing based on tester results."""
    messages = state["coder"]
    if messages.content.lower().contains("shaka"):
        return "developer"  # If error found, return to developer
    return "document"


# Define workflow edges
graph.add_edge(START, "analyst")
graph.add_edge("analyst", "developer")
graph.add_edge("developer", "tester")
graph.add_conditional_edges(
    "tester", checker, {"developer": "developer", "document": "document"}
)
graph.add_edge("document", END)

grapher = graph.compile()

# Streamlit App
st.title("Software Workflow Automation Designed By Arash")

# Sidebar with Graph Visualization
sidebar = st.sidebar
sidebar.title("Workflow Diagram")
with sidebar:
    grapher.get_graph(xray=True).draw_mermaid_png(output_file_path="graph.png")
    sidebar.image("graph.png")
# Display graph in sidebar

# User input
user_input = st.text_area("Enter requirements:")

if st.button("Run Workflow") and user_input:
    state = {"topic": [HumanMessage(content=user_input)]}
    response = grapher.invoke(state)
    st.header("Results Just Came out")
    with st.spinner("Wait for it...", show_time=True):
        time.sleep(3)
    st.markdown(response["documenter"], unsafe_allow_html=True)
