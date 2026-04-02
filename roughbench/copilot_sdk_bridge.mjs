import process from "node:process";
import { pathToFileURL } from "node:url";

async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) {
    chunks.push(chunk);
  }
  return Buffer.concat(chunks).toString("utf8");
}

async function stopClient(client) {
  const stopPromise = client.stop();
  const timeout = new Promise((resolve) => {
    setTimeout(() => resolve("timeout"), 5000);
  });
  const result = await Promise.race([stopPromise, timeout]);
  if (result === "timeout") {
    await client.forceStop();
  }
}

try {
  const rawInput = await readStdin();
  const request = JSON.parse(rawInput);
  const {
    sdk_module_path: sdkModulePath,
    cli_path: cliPath,
    cwd,
    model,
    reasoning_effort: reasoningEffort,
    system_prompt: systemPrompt,
    user_prompt: userPrompt,
    timeout_ms: timeoutMs,
    log_level: logLevel,
  } = request;

  if (!sdkModulePath || !cliPath || !model || !systemPrompt || !userPrompt) {
    throw new Error("Missing required Copilot bridge fields.");
  }

  const { CopilotClient, approveAll } = await import(pathToFileURL(sdkModulePath).href);
  const client = new CopilotClient({
    cliPath,
    useStdio: true,
    cwd: cwd || process.cwd(),
    logLevel: logLevel || "error",
  });

  let session;
  try {
    await client.start();
    const auth = await client.getAuthStatus();
    if (!auth?.isAuthenticated) {
      throw new Error("Copilot CLI is not authenticated.");
    }

    session = await client.createSession({
      clientName: "roughbench",
      model,
      reasoningEffort: reasoningEffort || undefined,
      onPermissionRequest: approveAll,
      tools: [],
      availableTools: [],
      streaming: false,
      workingDirectory: cwd || process.cwd(),
      systemMessage: {
        mode: "replace",
        content: systemPrompt,
      },
    });

    const response = await session.sendAndWait(
      { prompt: userPrompt },
      Number.isFinite(timeoutMs) ? timeoutMs : 120000,
    );

    let content = response?.data?.content?.trim() || "";
    if (!content) {
      const messages = await session.getMessages();
      for (let index = messages.length - 1; index >= 0; index -= 1) {
        const message = messages[index];
        if (message.type === "assistant.message" && message.data?.content) {
          content = String(message.data.content).trim();
          if (content) {
            break;
          }
        }
      }
    }

    process.stdout.write(
      JSON.stringify({
        content,
        session_id: session.sessionId,
        model,
      }),
    );
  } finally {
    if (session) {
      try {
        await session.disconnect();
      } catch {
        // Ignore disconnect cleanup failures; the client stop handles process cleanup.
      }
    }
    await stopClient(client);
  }
} catch (error) {
  const detail = error instanceof Error ? error.stack || error.message : String(error);
  process.stderr.write(detail);
  process.exit(1);
}
