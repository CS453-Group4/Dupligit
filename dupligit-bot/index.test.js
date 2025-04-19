import { createRequire } from "module";
const require = createRequire(import.meta.url);

import appFn from "./index.js"; // Your Probot app logic
import { Probot } from "probot";

// Use `nock` to prevent real GitHub API calls
const nock = require("nock");
nock.disableNetConnect();

const run = async () => {
  const probot = new Probot({
    appId: "123",
    privateKey: "test",
    githubToken: "test",
  });

  // Load your bot logic
  probot.load(appFn);

  // Simulate an issue opened event
  await probot.receive({
    name: "issues",
    id: "test-id",
    payload: {
      action: "opened",
      issue: {
        number: 42,
        title: "App crashes on profile click",
      },
      repository: {
        owner: { login: "test-user" },
        name: "test-repo",
      },
    },
  });
};

run();
