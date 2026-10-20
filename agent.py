import os
import json
from dotenv import load_dotenv
import anthropic
from tools import get_weather

# ── Load the API key from .env ──────────────────────────────
load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ── Tell Claude what tools it has ───────────────────────────
# This is the "menu" of tools we hand to the API.
# Claude reads the description and decides when to call it.
TOOLS = [
    {
        "name": "get_weather",
        "description": (
            "Fetches real-time weather data and rain probability for a given city. "
            "Returns temperature, humidity, wind speed, current conditions, "
            "and the chance of rain over the next 6 hours."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "The city name to get weather for, e.g. 'Cebu', 'Manila', 'Talisay'",
                }
            },
            "required": ["city"],
        },
    }
]

# ── The agent loop ───────────────────────────────────────────
def run_weather_agent(user_message: str, max_steps: int = 5) -> str:
    """
    Runs the agent loop:
      1. Send user message to Claude
      2. If Claude wants to call a tool → run it → feed result back
      3. Repeat until Claude gives a final text answer
    """
    messages = [{"role": "user", "content": user_message}]

    print(f"\n{'='*50}")
    print(f"🤖 Agent starting...")
    print(f"{'='*50}")

    for step in range(max_steps):
        print(f"\n── Step {step + 1} ──")

        # Ask Claude what to do
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            tools=TOOLS,
            messages=messages,
            system=(
                "You are a friendly weather assistant. "
                "When asked about weather or rain, always use the get_weather tool "
                "to fetch real data first. Then give a clear, helpful summary "
                "including: current conditions, temperature, and rain chances. "
                "Add a practical tip (e.g. 'bring an umbrella' or 'great day for a walk')."
            ),
        )

        print(f"   Stop reason: {response.stop_reason}")

        # ── Case 1: Claude wants to call a tool ──────────────
        if response.stop_reason == "tool_use":
            # Add Claude's response to history
            messages.append({"role": "assistant", "content": response.content})

            # Find the tool call block(s) and execute them
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_name  = block.name
                    tool_input = block.input
                    tool_id    = block.id

                    print(f"   🔧 Calling tool: {tool_name}({tool_input})")

                    # Run the actual Python function
                    if tool_name == "get_weather":
                        result = get_weather(tool_input["city"])
                    else:
                        result = {"error": f"Unknown tool: {tool_name}"}

                    print(f"   📦 Tool result: {json.dumps(result, indent=6)}")

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": json.dumps(result),
                    })

            # Feed all tool results back to Claude
            messages.append({"role": "user", "content": tool_results})

        # ── Case 2: Claude is done — return the final answer ─
        elif response.stop_reason == "end_turn":
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text += block.text

            print(f"\n{'='*50}")
            print("✅ Agent finished!")
            print(f"{'='*50}\n")
            return final_text

        else:
            # Unexpected stop reason
            return f"Agent stopped unexpectedly: {response.stop_reason}"

    return "⚠️ Reached max steps without a final answer."


# ── Entry point ──────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🌤️  Weather Agent")
    print("─" * 40)
    print("Ask about weather in any city.")
    print("Type 'quit' to exit.\n")

    while True:
        user_input = input("You: ").strip()

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye! 👋")
            break

        answer = run_weather_agent(user_input)
        print(f"\n🤖 Agent: {answer}\n")
