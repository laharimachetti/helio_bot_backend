from fastapi import FastAPI, Request
from recommendation_helper import get_recommendations
from formatter import format_response
from fastapi.middleware.cors import CORSMiddleware
import re

app = FastAPI()

# =====================================================
# CORS
# =====================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# STATE & CACHE
# =====================================================
user_state = {}        # session -> {rank, branch}
response_cache = {}   # session_rank_branch -> response


# =====================================================
# BRANCH FALLBACK EXTRACTION
# =====================================================
def extract_branch_from_text(text: str):
    t = text.lower()
    if "cse" in t or "computer" in t:
        return "CSE"
    if "it" in t or "information" in t:
        return "IT"
    if "ece" in t or "electronics" in t:
        return "ECE"
    if "eee" in t or "electrical" in t:
        return "EEE"
    if "mech" in t or "mechanical" in t:
        return "Mechanical"
    if "civil" in t:
        return "Civil"
    return None


# =====================================================
# INTENT HELPERS
# =====================================================
def is_greeting(text: str):
    return text.strip().lower() in ["hi", "hello", "hey", "hii", "hai"]

def wants_restart(text: str):
    t = text.lower()
    return any(p in t for p in [
        "start new",
        "start a new",
        "start with new",
        "new rank",
        "new recommendation",
        "start over",
        "restart",
        "reset"
    ])

def wants_new_branch(text: str):
    t = text.lower()
    return any(p in t for p in [
        "check another branch",
        "another branch",
        "change branch",
        "different branch"
    ])


def is_exit(text: str):
    t = text.lower()
    return any(p in t for p in [
        "bye", "bye bye", "goodbye"
    ])

def is_acknowledgement(text: str):
    return text.strip().lower() in [
        "ok", "okay", "fine", "cool",
        "thanks", "thank you", "thx"
    ]


# =====================================================
# WEBHOOK
# =====================================================
@app.post("/webhook")
async def dialogflow_webhook(request: Request):
    data = await request.json()

    session = data.get("session", "default")
    text = data.get("message", "")
    params = {}


    # INIT SESSION
    if session not in user_state:
        user_state[session] = {"rank": None, "branch": None}

    state = user_state[session]

    # -------------------------------------------------
    # GREETING
    # -------------------------------------------------
    if is_greeting(text):
        user_state[session] = {"rank": None, "branch": None}
        return { "fulfillmentText": "Welcome! I'm Helio-Bot. <br> I can help you with college and branch recommendations.\n" }

    # -------------------------------------------------
    # RESTART
    # -------------------------------------------------
    if wants_restart(text):
        user_state[session] = {"rank": None, "branch": None}
        return {
            "fulfillmentText":
            "No problem 😊 Let’s start fresh.\n"
            "What is your rank?"
        }

    if wants_new_branch(text):
        state["branch"] = None
        return {
            "fulfillmentText":
            f"Okay Your rank is {state['rank']}.\n"
            "Now which branch would you like to check? (CSE, ECE, IT, etc.)"
    }
    # -------------------------------------------------
    # EXIT
    # -------------------------------------------------
    if is_exit(text):
        user_state.pop(session, None)
        response_cache.clear()
        return {
            "fulfillmentText":
            "You’re welcome 😊\n"
            "All the best!\n"
            "If you need help again, just say hi 👋"
        }

    # -------------------------------------------------
    # ACKNOWLEDGEMENTS (CRITICAL FIX)
    # -------------------------------------------------
    if is_acknowledgement(text):
        return {
            "fulfillmentText":
            "Glad I could help 😊\n"
            "If you’d like to check another branch or start a new recommendation, just tell me."
        }

    # -------------------------------------------------
    # EXTRACT RANK
    # -------------------------------------------------
    rank = params.get("rank")
    if not rank:
        match = re.search(r"\b\d{4,6}\b", text)
        if match:
            rank = match.group()

    if rank:
        try:
            state["rank"] = int(rank)
        except:
            pass

    if state["rank"] is None:
        return {
            "fulfillmentText":
            "Sure 🙂 To suggest suitable colleges, please tell me your rank."
        }

    # -------------------------------------------------
    # EXTRACT BRANCH
    # -------------------------------------------------
    branch = params.get("branch")
    if branch and isinstance(branch, str) and branch.lower() != "required":
        state["branch"] = branch.strip()
    else:
        extracted = extract_branch_from_text(text)
        if extracted:
            state["branch"] = extracted

    if state["branch"] is None:
        return {
            "fulfillmentText":
            f"Got it 👍 Your rank is {state['rank']}.\n"
            "Do you have a preferred branch? (CSE, ECE, IT, etc.)"
        }

    # -------------------------------------------------
    # CACHE (SESSION SAFE)
    # -------------------------------------------------
    cache_key = f"{session}_{state['rank']}_{state['branch'].lower()}"
    if cache_key in response_cache:
        return response_cache[cache_key]

    # -------------------------------------------------
    # GET RECOMMENDATIONS
    # -------------------------------------------------
    results = get_recommendations(state["rank"], state["branch"])
    response = format_response(results, state["rank"], state["branch"])

    response_cache[cache_key] = response
    return response
