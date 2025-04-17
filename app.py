import os
import uuid  # To generate unique thread IDs
from dotenv import load_dotenv
from typing import TypedDict, Literal
from langchain_groq import ChatGroq
from langchain_ollama.chat_models import ChatOllama
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from typing import Annotated, List
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver  # Added memory saving

load_dotenv()

os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")


class State(TypedDict):
    messages: Annotated[List, add_messages]


graph = StateGraph(State)
llm = ChatOllama(id="llama3.2:1b")
memory = MemorySaver()  # Memory saver initialized


def create_node(state, system):
    human_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
    ai_messages = [msg for msg in state["messages"] if isinstance(msg, AIMessage)]
    sys_messages = [SystemMessage(content=system)]
    messages = sys_messages + human_messages + ai_messages
    message = llm.invoke(messages)
    return {"messages": [message]}


analyst = lambda state: create_node(
    state,
    "You are a software requirements analyst. Review the provided instructions and generate clear requirements for a developer .",
)
developer = lambda state: create_node(
    state,
    "You are a senior Python developer. Review the provided requirements and generate advanced and error-free code from it",
)
tester = lambda state: create_node(
    state,
    "You are a tester. Check the developer's code for errors, and if any are found, you are going to give the error to developer . Otherwise, confirm that the code is error-free and just say 'developer Good'.",
)
document = lambda state: create_node(
    state,
    "You are an expert in creating technical documentation and can Summarize complex documents into human-readable documentation. Review the messages and create a meaningful summary while retaining all generated source code.",
)

graph.add_node("analyst", analyst)
graph.add_node("developer", developer)
graph.add_node("tester", tester)
graph.add_node("document", document)


def checker(state: State) -> Literal["developer", "document"]:
    messages = state["messages"]
    last_message = messages[-1]
    if isinstance(last_message, AIMessage) and "error" in last_message.content.lower():
        return "developer"  # If error found, send back to developer
    return "document"


graph.add_edge(START, "analyst")
graph.add_edge("analyst", "developer")
graph.add_edge("developer", "tester")
graph.add_conditional_edges("tester", checker)
graph.add_edge("document", END)


grapher = graph.compile()  # ✅ Now memory tracking works

try:
    grapher.get_graph(xray=True).draw_mermaid_png(output_file_path="graph.png")
except Exception as e:
    print(f"Error in saving graph image: {e}")


def main():

    while True:
        user_input = input("Say: ")
        if user_input.lower() in ["q", "exit"]:
            print("Goodbye!")
            break

        response = grapher.invoke(
            {"messages": [HumanMessage(content=user_input)]})

        all_messages = response["messages"]

        if len(all_messages) >= 4:
            print("\nAnalyst: ", all_messages[-4].content)
            print("-" * 50)

        if len(all_messages) >= 3:
            print("Developer: ", all_messages[-3].content)
            print("-" * 50)

        if len(all_messages) >= 2:
            print("Tester: ", all_messages[-2].content)
            print("-" * 50)

        if len(all_messages) >= 1:
            print("Document: ", all_messages[-1].content)
            print("-" * 50)


if __name__ == "__main__":
    main()
