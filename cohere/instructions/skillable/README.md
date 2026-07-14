# Welcome to **Build AI Agents with Cohere in Microsoft Foundry (Model Mastery)**

In this workshop you'll use **Cohere** models running on **Microsoft Foundry** to build and explore a real AI application.

You'll work through two labs:

- **Lab 1: Build a travel concierge.** You'll assemble a team of AI agents that plan a business trip, then make them observable, measurable, and safe.
- **Lab 2: Explore Cohere capabilities.** You'll see how different Cohere models solve different problems: searching by meaning, searching images, and re-sorting results.

>[!Knowledge] An **agent** is a program that uses an AI model to decide what to do and which tools to call, rather than following a fixed script. A **model** is the AI itself; Foundry is where the models are hosted.

The next few pages get you set up: sign in to the lab computer, open the project, and learn how to run a notebook. Then you'll start Workshop 1.

===

# Sign in to the Virtual Machine

1. [] Sign in to the VM with the following credentials:
	
  **Username**: +++@lab.VirtualMachine(Windows11).Username+++  
   **Password**: +++@lab.VirtualMachine(Windows11).Password+++

>[!tip] Select the keyboard symbol next to the text to type it into the VM.

# Open the project in Visual Studio Code

You'll do all of your work in **Visual Studio Code** (VS Code), the editor on
the desktop.

1. [] On the desktop, select the **Visual Studio Code** icon to open it.
1. [] Confirm the file explorer on the left shows the **cohere-azure-workshops** project, with folders named **lab-1-foundry-maf** and **lab-2-cohere-capabilities**.

    !IMAGE[8rg4wiop.png](instructions347670/8rg4wiop.png)

	>[!Hint] If VS Code opens but does not show those folders, open the project folder manually:
    - Select **File** then **Open Folder**.
    - Go to `C:\LabFiles\cohere-azure-workshops` and select **Select Folder**.
    - If asked whether you trust the authors, choose **Yes, I trust the authors**.

	>[!Knowledge] The project contains two lab folders. You'll open notebooks from inside these folders during the workshop. Keep VS Code open for the duration of the lab.

===
# How to run the notebooks

Each lab is a set of **notebooks**: documents that mix explanation with runnable code cells.

**To run a cell:** select it, then press **Shift+Enter**. The cell runs and moves to the next one.

**Always run cells in order, top to bottom**, in each notebook. Later cells depend on earlier ones.

**Reading the status of a cell:**

- A number in brackets such as `[1]` means the cell finished successfully.
- A spinning circle means the cell is running. Wait for it to complete.
- The word **Pending** means the cell is waiting for the environment to be ready. If it stays Pending for more than a few seconds, select **Restart** at the top of the notebook, then run the cell again.

>[!tip] If you see a message that the output is truncated, select **scrollable element** to view all of it. This is normal when a cell prints a lot of text.

>[!Alert] These notebooks make live calls to shared Cohere model deployments. Run cells one at a time and read the output as you go. If you ever see a "too many requests" message, wait a few seconds and run that cell again.

>[!tip] **Free resources between notebooks.** Each notebook runs in its own kernel that keeps models, data, and connections in memory. When you finish a notebook-or before re-running one from the top-clear its resources: select **Restart** at the top of the notebook to reset the kernel, and use **Clear All Outputs** if you want a clean slate. This frees memory on the VM and prevents leftover state from carrying between runs.


##Let's get started!##

===

# Workshop 1: Build a Travel Concierge

**What you'll build:** a travel desk staffed by four AI agents. Three specialists each handle one part of a trip (flights, hotels, cars), and one concierge coordinates them.

>[!Knowledge] Microsoft Foundry can run an agent two ways: it can host the agent for you, or you can run it in your own code. In this lab you'll build the concierge in your own code with the **Microsoft Agent Framework** and point it at your Cohere model in Foundry. Running it yourself gives you full control over how the agents are orchestrated and observed. Same model, your own code.

You'll work through five notebooks: verify, build, trace, evaluate, and red-team. The whole lab takes about **60 minutes**.

---

## Notebook 01: Verify the model

**Goal:** confirm your code can reach the Cohere model before building anything on it.

>[!note] Reminder: free resources as you go-select **Restart** at the top of any finished notebook before running the next one.

1. [] Open **`01-verify-cohere.ipynb`**.

	!IMAGE[5x2xyra6.png](instructions347670/5x2xyra6.png)

1. [] Open a new terminal using **Terminal > New Terminal**. It will open at the bottom center of VS Code.

	!IMAGE[oi3snrp4.png](instructions347670/oi3snrp4.png)

1. [] Send `az login` in the terminal.

	!IMAGE[ust4w5pi.png](instructions347670/ust4w5pi.png)

1. [] Minimize VS Code by selecting it from the toolbar.

	!IMAGE[w2s6qfk4.png](instructions347670/w2s6qfk4.png)

1. [] Choose **Work or school account** and select **Continue**.
	
  !IMAGE[2lw561sr.png](instructions347670/2lw561sr.png)

1. [] Sign in with the following credentials:

	**Azure Username**: +++@lab.CloudPortalCredential(User1).Username+++  
	**TAP**: +++@lab.CloudPortalCredential(User1).AccessToken+++

1. [] Select **Yes**, then return to VS Code. 
	
  !IMAGE[6df8lttl.png](instructions347670/6df8lttl.png)

1. [] In the terminal, select the default subscription:

	!IMAGE[ks7zq7hj.png](instructions347670/ks7zq7hj.png)

	>[!note] Close the terminal once logged in.
  !IMAGE[zru9azd5.png](instructions347670/zru9azd5.png)

1. [] Run each cell in order, reading the short notes between them. 

	!IMAGE[zrm8fc7r.png](instructions347670/zrm8fc7r.png)

1. [] The first time you execute a cell you'll see a message like this: 
	
  !IMAGE[xvf2hvzv.png](instructions347670/xvf2hvzv.png)

	>[!note] Select **Allow**.

1. [] Confirm each cell prints a reasonable output and/or a sensible reply from the model.!IMAGE[mfyt53vz.png](instructions347670/mfyt53vz.png)  !IMAGE[w56l55if.png](instructions347670/w56l55if.png)

	>[!note] Look for something like this:
!IMAGE[hohcz8ot.png](instructions347670/hohcz8ot.png)  
If a cell fails with an authentication error, return to the welcome page and run `az login` again.

>[!Knowledge] This notebook opens a chat connection to the Cohere `command-a-plus` model and sends one message. If you get a reply, the connection works and you're ready to build.

===

## Notebook 02: Build the multi-agent concierge

**Goal:** assemble the three specialist agents and the concierge that coordinates them, then plan a full trip.

>[!note] Reminder: before you start, **Restart** the kernel of the previous notebook to free its resources.

1. [] Open **`02-build-multi-agent.ipynb`**.

	!IMAGE[x2ti0ak0.png](instructions347670/x2ti0ak0.png)

1. [] Run the cell that prepares the notebook and the one that builds the three specialists (flight, hotel, car).

	!IMAGE[pm9acawj.png](instructions347670/pm9acawj.png)
	!IMAGE[oooqf72o.png](instructions347670/oooqf72o.png)

1. [] Run the cell that tries one specialist on its own.

	!IMAGE[a0lxdhme.png](instructions347670/a0lxdhme.png)

1. [] Run the cell that assembles the concierge and plan a multi-leg trip.

	!IMAGE[rwtf6eky.png](instructions347670/rwtf6eky.png)

1. [] Finally, execute the cells that run a multi-leg trip end-to-end.

	!IMAGE[3629t9bg.png](instructions347670/3629t9bg.png)
	!IMAGE[vr47v5ow.png](instructions347670/vr47v5ow.png)

	>[!tip] These last cells will take about a minute to complete. All the orchestration is happening right now. We haven't surfaced yet what's going on under the hood, but don't worry, you'll see that later on in the **Observability** part.

>[!Knowledge] The concierge does not book flights or hotels itself. It calls each specialist as if the specialist were a single tool, and the specialist decides what to do. This pattern is called **agents as tools**, and it is a clean way to coordinate several agents from one place.

**What to notice:** watch the concierge hand off each leg of the trip to the right specialist.

===

## Notebook 03: Trace the concierge

**Goal:** Turn on tracing so you can see the exact path a request takes through the agents.

>[!note] Reminder: before you start, **Restart** the kernel of the previous notebook to free its resources.

1. [] Open **`03-trace-multi-agent.ipynb`**.

	!IMAGE[4nto66aj.png](instructions347670/4nto66aj.png)

1. [] Run the cells that configure tracing and capture the activity.

1. [] Run the concierge with tracing on, then read the resulting trace. After a few seconds, you should see some telemetry.

	!IMAGE[aipov8ki.png](instructions347670/aipov8ki.png)

1. [] Run the last cell, so you see the information that has been traced by the action of the agent, now in table format.

1. [] In the output from the last cell, select **text editor** to open the output in a text editor for a more complete view.

	!IMAGE[sqq730gw.png](instructions347670/sqq730gw.png)

>[!Knowledge] **Tracing** records every step a request takes: each agent turn and each tool call. It answers the question "how did the concierge arrive at this answer?" This is one of three things you'll check in this lab: tracing shows *how it happened*, evaluation shows *how good* it is, and red-teaming shows *how safe* it is.

===

## Notebook 04: Evaluate in four rounds (OPTIONAL)

**Goal:** measure answer quality with the same test set across four versions of the agent, so you can see each improvement clearly.

You'll run four notebooks. Each uses the same set of test questions and the same scoring, so the results are comparable. Only the agent changes between rounds.

>[!note] Reminder: these rounds run back-to-back-**Restart** each round's kernel before starting the next one to free its resources.

1. [] **Round 1, baseline.** Open **`04-eval-round1-baseline.ipynb`** and run it. A plain agent with generic instructions. This sets your starting scores.
2. [] **Round 2, grounded.** Open **`04-eval-round2-grounded.ipynb`** and run it. The same agent, now given the travel policy and catalog details. Compare the scores against Round 1.
3. [] **Round 3, policy check.** Open **`04-eval-round3-policy-evaluator.ipynb`** and run it. Adds a custom check that grades each answer against the travel policy.
4. [] **Round 4, full concierge.** Open **`04-eval-round4-multi-agent.ipynb`** and run it. Swaps in the full multi-agent concierge with booking tools.

>[!Knowledge] Keeping the test questions and the scoring identical across all four rounds is what makes the comparison fair. You can see exactly what grounding, a custom policy check, and multi-agent coordination each add.

>[!tip] After each round, glance at the scores before moving on. The story is in how they change from round to round.

===

## Lab 1, Notebook 05: Red-team the concierge (OPTIONAL)

**Goal:** test whether the concierge can be tricked into unsafe behavior.

>[!note] Reminder: before you start, **Restart** the kernel of the previous notebook to free its resources.

1. [] Open **`05-local-redteam.ipynb`**.
2. [] Run the cell that wraps the concierge as a target for the scan.
3. [] Run the scan, then review the findings.

>[!Knowledge] A **red-team scan** sends adversarial prompts that try to make the agent break its rules, like a mystery shopper testing a help desk. The scan runs on your machine against your local concierge, and you review the findings right in the notebook.

**Lab 1 complete.** You built a Cohere-powered concierge, traced it, evaluated it across four rounds, and tested its safety.

===

# Lab 2: Explore Cohere Capabilities

Currently, the travel concierge from Lab 1 relies on keyword-based search to find matches. We can improve the search functionality by bringing in two powerful ML models from Cohere: the Cohere vector embedding model and the Cohere re-ranking model.

Using the vector embedding model, we can extend the search to go beyond keyword-only searches and search by semantic similarity instead. Since the model supports multimodal embeddings, we can even use it to search images.

Using the re-ranking model, we can refine the search results that come back from the vector search. The re-ranking model looks at each result, scores it according to the user's original query, and outputs a re-ranked list of results.

>[!Knowledge] An **embedding** encodes text or an image as a vector of numbers: similar meanings get encoded into vectors that sit closer together in a multi-dimensional vector space, so you can find things by meaning instead of exact words. **Rerank** takes a first shortlist and sorts it again using a more detailed need. **Multimodal** means the same embedding works on images, such as charts, not just text.

**How each capability helps the concierge:**

| If the concierge could ... | The Cohere capability | Notebook |
| --- | --- | --- |
| find trips that feel like a past good one, even if worded differently | search by meaning (embeddings) | 2a |
| search charts and business-graph images, not just text | multimodal embeddings | 2b |
| re-sort hotels after you say "no red-eyes, and I need a gym" | rerank | 2c |

This lab takes about **45 minutes**.

>[!Alert] Open each Lab 2 notebook from inside the **lab-2-cohere-capabilities** folder, so the data and image files it needs are found correctly. Your environment is set up for this; just open the notebook and run.

===

## Lab 2, Notebook 2a: Search by meaning (embeddings)

**Goal:** turn text into embeddings and measure how close two pieces of text are in meaning.

>[!note] Reminder: before you start, **Restart** the kernel of the previous notebook to free its resources.

1. [] Open **`lab-2a-embed.ipynb`** from the **lab-2-cohere-capabilities** folder.
2. [] Run the quick test cell to confirm the connection.
3. [] Run the cells that embed several texts and compare their similarity.
4. [] Run the multilingual cells and notice the same idea in different languages scores as similar.

>[!Knowledge] This is the foundation of **semantic search**: because similar meanings get encoded as vectors that sit close together in the vector space, you can find relevant content even when it uses different words than your query.

===

## Lab 2, Notebook 2b: Search images (multimodal)

**Goal:** index images of business graphs and search them by meaning.

>[!note] Reminder: before you start, **Restart** the kernel of the previous notebook to free its resources.

1. [] Open **`lab-2b-embed.ipynb`** from the **lab-2-cohere-capabilities** folder.
2. [] Run the cells that index the graph images into a local search store.
3. [] Run the three search examples and see the best-matching image returned for each query.

>[!Knowledge] Embed v4 is **multimodal**: it encodes images into the same kind of vector as text, so you can search a pile of charts and graphs by describing what you want. This is Cohere's standout feature and removes the need to manually tag or parse images.

>[!Hint] If a cell reports a missing file, you likely opened the notebook from the wrong folder. Close it and reopen it from inside the **lab-2-cohere-capabilities** folder.

===

## Lab 2, Notebook 2c: Re-sort results (rerank)

**Goal:** improve a list of results by re-sorting it against a more detailed query.

>[!note] Reminder: before you start, **Restart** the kernel of the previous notebook to free its resources.

1. [] Open **`lab-2c-rerank-getting-started.ipynb`** from the **lab-2-cohere-capabilities** folder.
2. [] Run the first rerank example on a plain-text list.
3. [] Run the multilingual, numeric, and time-based examples.

>[!Knowledge] **Rerank** reads your query and each candidate together, so it catches relevance that a plain similarity search misses, including hard cases involving other languages, numbers, dates, and negation ("not a red-eye"). Use it as the final sharpening step after a first search.

**What to notice:** the most relevant result rises to the top after reranking, even when it did not start there.

===

## Optional deep-dives

If time allows, two extra rerank notebooks go further. They reinforce the idea rather than introduce new concepts, so skip them if the session is tight.

>[!note] Reminder: as with the other notebooks, **Restart** the previous notebook's kernel before running these to free its resources.

1. [] *(Optional)* **`optional-lab-rerank_structured_data.ipynb`**: rerank structured records such as emails and table rows.
2. [] *(Optional)* **`optional-lab-rerank_wikipedia_search.ipynb`**: rerank the results of a plain keyword search.

===

# What you learned

You have completed the workshop. To recap:

- **Lab 1:** you built a Cohere-powered multi-agent concierge with the Microsoft Agent Framework, then traced it, evaluated it across four rounds, and red-teamed it for safety.
- **Lab 2:** you saw when to use each Cohere capability:
  - **Embeddings** for finding things by meaning.
  - **Multimodal embeddings** for searching images such as charts and graphs.
  - **Rerank** for re-sorting a shortlist against a detailed need.

>[!Knowledge] One practical note to remember: these Cohere models are called on Foundry through the Cohere routes (the `cohere` client pointed at a `/providers/cohere` address).

Thank you for attending. You now have a working pattern for building, measuring, and improving Cohere-powered applications on Microsoft Foundry.
