from langgraph.graph import StateGraph,START,END
from typing import TypedDict,Literal,Annotated
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage,HumanMessage
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

generaterllm=ChatOpenAI(model_name="gpt-4o")
evaluatorllm=ChatOpenAI(model_name="gpt-4o-mini")
optimizerllm=ChatOpenAI(model_name="gpt-4o")

class TweetState(TypedDict):
    topic:str
    GeneratedTweet:str
    Evaluation: Literal["Approved","NeedsImprovement"]
    feedback:str
    Iteration:int
    maxIteration:int

class Evaluation(BaseModel):
    Evaluation: Literal["Approved","NeedsImprovement"] = Field(description="Evaluation of the tweet")
    feedback:str = Field(description="Feedback for the tweet")


structured_evaluation_llm=evaluatorllm.with_structured_output(Evaluation)

def generate_tweet(state:TweetState):
    response= generaterllm.invoke([SystemMessage(content=f"You are a tweet generator for the topic {state['topic']}"),
    HumanMessage(content=f"""Generate Tweet in less than 200 characters on given topic {state['topic']} and give me in bullet points and they should be numbered
    dont use any symbols or html tags or markdown or any other formatting""")])
    return {"GeneratedTweet":response.content}

def evaluate_tweet(state:TweetState):
    response= structured_evaluation_llm.invoke([SystemMessage(content=f"You are a tweet evaluator for the topic {state['topic']}"),
    HumanMessage(content=f"""Ensure that the tweet is less than 200 characters and it is relevant to the topic {state['topic']} and it should be engaging and interesting and it should not contain any symbols or html tags or markdown or any other formatting""")])
    return {"Evaluation":response.Evaluation,"feedback":response.feedback}


def optimize_tweet(state:TweetState):
    response= optimizerllm.invoke([SystemMessage(content=f"You are a tweet optimizer for the topic {state['topic']}")])
    return {"GeneratedTweet":response.content,"Iteration":state["Iteration"]+1}

def route_evaluation(state:TweetState):
    if state["Evaluation"]=="Approved" or state["Iteration"]>=state["maxIteration"]:
        return "Approved"
    else:
        return "NeedsImprovement"



graph=StateGraph(TweetState) 
graph.add_node("GenerateTweet",generate_tweet)
graph.add_node("EvaluateTweet",evaluate_tweet)
graph.add_node("OptimizeTweet",optimize_tweet)

graph.add_edge(START,"GenerateTweet")
graph.add_edge("GenerateTweet","EvaluateTweet")
graph.add_conditional_edges("EvaluateTweet",route_evaluation,{"Approved":END,"NeedsImprovement":"OptimizeTweet"})
graph.add_edge("OptimizeTweet","EvaluateTweet")

workflow=graph.compile()

initial_state={
    "topic":"Phoenix Arizona",
    "GeneratedTweet":"",
    "Evaluation":"",
    "feedback":"",
    "Iteration":1,
    "maxIteration":3
}
result=workflow.invoke(initial_state)

print(result["GeneratedTweet"])
print(f"Total times interated {result['Iteration']}")



