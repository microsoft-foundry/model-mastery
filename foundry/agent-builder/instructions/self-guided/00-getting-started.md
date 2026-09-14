# 0 · Getting started

| Time | 5 mins |
|:---|:---|
|_Question:_  | I need to build a reliable AI agent — where do I start, and how will I know it's actually any good?| 
|_Goal:_| Get an overview for the workshop outline and driving scenario |
|||


> Welcome! <br/>
In this 90-minute workshop we'll help you answer the question using Microsoft Foundry tools and capabilities. Learn about model capabilities - and how to use them effectively. Learn about the agent development lifecycle (agent ops) - and how to optimize agents using a hill-climbing approach. Walk away with a sandbox for experimenting further.


<br/>

## 1. The scenario: assembling your AI agent

**Contoso Outdoors** is a fictitious enterprise company that specializes in hiking and camping gear for outdoor enthusiasts. They are currently preparing for a seasonal launch with a catalog of 10 products, each with a detailed manual. They want to deploy a customer support agent that can provide **accurate, grounded responses** to customer queries - in a friendly, polite way.

You are a new member of the Contoso Outdoors developer team building **TrailMate** - the friendly gear expert that customers can talk to, to get relevant and correct information about these new launches. 


## 2. The models: match the engine to the task

If an agent is the **car**, the model is the **engine**. Before you build the car, you need to know what engines are available - and which one fits the job. Picking the wrong model is like putting a lawnmower engine in a race car: it might run, but it won't get you where you need to go.

Different tasks need different model capabilities. We'll get a primer on three popular task types:

- **Chat completion** — general conversation and instruction-following. This is the workhorse for most agents: the customer asks a question, the model responds in natural language. → *Example: "Is the TrailWalker tent waterproof, and how many people does it sleep?"*
- **Reasoning** — multi-step thinking for harder problems (planning, comparison, analysis). These models "think" before they answer, trading extra latency and cost for stronger accuracy on complex tasks. → *Example: "I'm hiking a wet 3-day trail in October — compare the TrailWalker and SummitPro tents and tell me which to pack and why."*
- **Image generation** — turning a text prompt into an image, useful for visual product or marketing content. → *Example: "Create a hero banner of the TrailWalker tent pitched beside an alpine lake at sunrise for the seasonal launch page."*

You'll use the **model playground** to try deployed models against real tasks - so you can feel the differences in **capability** and adjust **configuration** (things like temperature, max tokens, and system prompt) before committing a model to your agent. Choosing with evidence, not reputation, is the first step in the journey.

## 3. The method: improve it by hill-climbing

Picking the engine is only the start. Once the car is running, you want to make it **reliable, cost-effective and performant** - and that means tuning. But any mechanic will tell you: if you swap the engine, adjust the tires, and change the fuel all at once, then take it for a spin, you'll never know *which* change made it faster. You tune **one thing at a time**, and you need a **diagnostic** - a lap time, a dyno reading - to confirm the change actually did what you hoped.

Agents are no different. You want to start with something that works, then improve it in steps to reach the desired targets. Your diagnostic is an evaluation rubric that grades progress on multiple dimensions. We'll use a "hill climbing" analogy to define that same one-change-at-a-time optimization journey:

1. **Measure your current altitude** — score the agent using a defined rubric. That's your baseline.
2. **Take one step** — change exactly one thing about the agent (the model, *or* the
   instructions).
3. **Measure again** — did you move up in altitude? Keep the change only if the evidence says so.

What does the evaluation rubric look like? Think of it as a weighted score across multiple dimensions. For instance three quality bars define "good" for TrailMate: it must be **grounded** (answers come from the manuals), **correct**, and **honest** (it refuses when the manuals don't cover something).

## 4. What you'll do

You'll take TrailMate on the full journey - from choosing an engine to tuning the car - and get hands-on with Microsoft Foundry models and tooling along the way:

1. **Model understanding** — *learn about engines*: try the deployed models in the playground and pick the right engine for the task, with evidence.
1. **Agent building** — *go from engine to car*: turn that model into a working agent grounded in your product manuals and spec, observe it through traces and metrics, and run a baseline evaluation to set your starting altitude.
1. **Agent optimization** — *tune the car, one measurable change at a time*, and re-measure after each:
   - **Model Router** — *don't pick the engine, let your pit crew decide*: hand off to a smart router that picks a model per request.
   - **Agent Optimizer** — *find different candidates for a climb and pick the winner*: look at the metrics and let it propose sharper instructions, guided by the rubric.
1. **Agent versioning** — promote the winner to be the new baseline: keep the change the evidence supports and climb again from there.


## 5. How the pieces fit

Here's the toolkit you'll use to make it all happen:

- **Microsoft Foundry** — hosts the models, the playground, the evaluations, and the optimizer.
- A **prompt agent** — TrailMate itself: a model + instructions + tools, working together.
- The **manuals** — your source of truth, so answers stay grounded.
- The **eval dataset + rubric** — your diagnostic for measuring quality after every change.

➡️ Next: [Set up and validate](01-setup-and-validate.md)
