# Third-party notices

This project incorporates material from the projects below. Each is used under
the MIT License, reproduced in full at the end of this file.

## Code with Claude Foundry Workshop

- Repository: https://github.com/hnky/code-with-claude-foundry-workshop
- Copyright (c) 2026 Henk Boelman
- SPDX-License-Identifier: MIT
- License: https://github.com/hnky/code-with-claude-foundry-workshop/blob/main/LICENSE

The workshop this project builds on. Used in:

| File | What is derived |
| --- | --- |
| `sparkles-agent/agent.py` | Client setup and the agent loop, from `workshop/sample-code/agent.py` |
| `skillable/lab1/`, `skillable/lab2/` | The one-page-per-module structure, following `workshop/skillable/` |

## Claude on Foundry hands-on workshop (Foundry IQ sample)

- Repository: https://github.com/ShilJain/Claude-on-foundry-handsonworkshop
- Copyright (c) 2026 Shilpa Jain
- SPDX-License-Identifier: MIT
- License: https://github.com/ShilJain/Claude-on-foundry-handsonworkshop/blob/main/LICENSE

The Foundry IQ knowledge base work. Used in:

| File | What is derived |
| --- | --- |
| `foundry-iq/docs/cupcake-store-info.md` | The store policy document, adapted |
| `foundry-iq/ingest_foundry_iq.py` | The ingest and knowledge base creation calls, adapted |
| `eval-endpoint/cupcake-store-info.md` | The same store policy document, served by the eval endpoint |

## Cupcake Store MCP server

- Repository: https://github.com/GlobalAICommunity/cupcake-mcp
- Copyright (c) 2026 Global AI Community
- SPDX-License-Identifier: MIT
- License: https://github.com/GlobalAICommunity/cupcake-mcp/blob/main/LICENSE

The Cupcake Store MCP server used by Lab 1. **No code from this project is
included here.** It is deployed separately and referenced by URL;
`cupcake-mcp-setup.md` is a deployment runbook written for this workshop.

## MIT License

The following text applies to each of the projects above, with the copyright
holder named in that project's section.

```
MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
