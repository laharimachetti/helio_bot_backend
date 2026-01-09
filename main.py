from fastapi import FastAPI # type: ignore
from recommendation_helper import get_recommendations
from formatter import format_response
from pydantic import BaseModel # type: ignore
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware # type: ignore
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

# =========================
# REQUEST MODEL (THIS IS THE KEY FIX)
# =========================
class WebhookRequest(BaseModel):
    session: Optional[str] = "default"
    message: str


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
    return text.strip().lower() in ["hi", "hello", "hey", "hii", "hai", "hola"]

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
        "different branch",
        "other branch"
    ])


def is_exit(text: str):
    t = text.lower()
    return any(p in t for p in [
        "bye", "bye bye", "goodbye", "ok bye", "tata", "that's it"
    ])

def is_acknowledgement(text: str):
    return text.strip().lower() in [
        "ok", "okay", "fine", "cool", "thankyou", "Thankyou",
        "thanks", "thank you", "thx"
    ]


# =====================================================
# WEBHOOK
# =====================================================
@app.post("/webhook")
async def dialogflow_webhook(payload: WebhookRequest):
    
    session = payload.session or "default"
    text = (payload.message or "").strip()

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
    if state["rank"] is None:
        match = re.search(r"\b(\d{4,6})\b", text)
        if match:
            state["rank"] = int(match.group(1))

        else:
            return {
                "fulfillmentText":
                "Sure 🙂 To suggest suitable colleges, please tell me your rank."
            }

    # -------------------------------------------------
    # EXTRACT BRANCH
    # -------------------------------------------------
    if state["branch"] is None:
        branch = extract_branch_from_text(text)
        if branch:
            state["branch"] = branch
        else:
            return {
                "fulfillmentText":
                f"Got it 👍 Your rank is {state['rank']}.\n"
                "Do you have a preferred branch? (CSE, ECE, IT, etc.)"
            }

    # -------------------------------------------------
    # CACHE (SESSION SAFE)
    # -------------------------------------------------
    branch_key = state["branch"].lower() if state["branch"] else "unknown"
    cache_key = f"{session}_{state['rank']}_{branch_key}"

    if cache_key in response_cache:
        return response_cache[cache_key]

    # -------------------------------------------------
    # GET RECOMMENDATIONS
    # -------------------------------------------------
    if state["rank"] is None or state["branch"] is None:
        return {
            "fulfillmentText":
            "Please tell me your rank and preferred branch."
        }

    try:
        results = get_recommendations(state["rank"], state["branch"])
        response = format_response(results, state["rank"], state["branch"])
    
    except Exception as e:
        print("RECOMMENDATION ERROR:", e)
        return {
            "fulfillmentText":
            "Sorry, something went wrong while fetching recommendations.\n"
            "Please try again or restart."
        }

    response_cache[cache_key] = response
    return response