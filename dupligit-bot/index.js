import fetch from "node-fetch";
/**
 * This is the main entrypoint to your Probot app
 * @param {import('probot').Probot} app
 */
export default (app) => {
  // Your code here
  app.log.info("Yay, the app was loaded!");

  app.on("issues.opened", async (context) => {
    const issueTitle = context.payload.issue.title;
    app.log.info(`📩 New issue received: "${issueTitle}"`);
    let similarResponse;
    try {
      const res = await fetch(
        "https://420a-176-42-23-181.eu.ngrok.io/predict",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: issueTitle }),
        }
      );
      similarResponse = await res.json();
      app.log.info("🧠 Similarity result:", similarResponse);
    } catch (err) {
      console.error("❌ Error contacting backend:", err);
    }

    // Prepare a response comment
    let commentBody = "Thanks for opening this issue!";

    if (
      similarResponse?.most_similar &&
      similarResponse.similarity_score < 10 // ⬅️ Safety threshold (optional)
    ) {
      commentBody += `\n\n🤖 This might be similar to an existing issue:\n> "${
        similarResponse.most_similar
      }"\n🧠 Similarity score: ${similarResponse.similarity_score.toFixed(2)}`;
    } else {
      commentBody += `\n\n🔍 No strong duplicate candidates found.`;
    }

    // Post the comment on the issue
    await context.octokit.issues.createComment(
      context.issue({ body: commentBody })
    );
  });

  // For more information on building apps:
  // https://probot.github.io/docs/

  // To get your app running against GitHub, see:
  // https://probot.github.io/docs/development/
};
