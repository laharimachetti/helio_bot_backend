def format_response(results, rank, branch):
    if not results:
        return {
            "fulfillmentText":
            f"I couldn’t find suitable options for **{branch}** with rank **{rank}**.\n"
            "Would you like to try another branch?"
        }

    top_results = results[:5]

    text = f"🎓 Here are some **{branch} options** you may get with rank **{rank}**:\n\n"

    for r in top_results:
        text += f"• **{r['institute']}** – {r['academic_program']}\n"

    remaining = len(results) - len(top_results)
    if remaining > 0:
        text += f"\n…and **{remaining} more colleges** may also be possible.\n"

    text += (
    "\n👉 You can:\n"
    "• check another branch\n"
    "• start over with a new rank"
    )


    return {"fulfillmentText": text}
