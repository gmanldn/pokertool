# NeoVim Plugin

> [!NOTE]
> This plugin depends on the CLI tool. You should follow 
> [the CLI documentation](../cli/README.md) to install the CLI and familiarise 
> yourself with 
> [the basic usage of the CLI interface](../cli/README.md#getting-started) 
> before you proceed.

> [!NOTE]
> When the neovim plugin doesn't work properly, please try upgrading both the CLI
> and the neovim plugin to the latest version before opening an issue.


<!-- mtoc-start -->

* [Installation](#installation)
  * [Mason.nvim ](#masonnvim-)
  * [Nix](#nix)
  * [Lazy Loading](#lazy-loading)
* [Integrations](#integrations)
  * [milanglacier/minuet-ai.nvim](#milanglacierminuet-ainvim)
  * [olimorris/codecompanion.nvim](#olimorriscodecompanionnvim)
    * [Tools](#tools)
    * [Prompt Library](#prompt-library)
  * [CopilotC-Nvim/CopilotChat.nvim](#copilotc-nvimcopilotchatnvim)
    * [Setup](#setup)
    * [Configuration Options](#configuration-options)
    * [Usage Tips](#usage-tips)
    * [Performance Optimization](#performance-optimization)
    * [Using with Sticky Prompts](#using-with-sticky-prompts)
  * [Status Line Component](#status-line-component)
    * [nvim-lualine/lualine.nvim](#nvim-lualinelualinenvim)
    * [heirline.nvim](#heirlinenvim)
  * [fidget.nvim](#fidgetnvim)
  * [Model Context Protocol (MCP)](#model-context-protocol-mcp)
* [Configuration](#configuration)
  * [`setup(opts?)`](#setupopts)
* [User Command](#user-command)
  * [`VectorCode register`](#vectorcode-register)
  * [`VectorCode deregister`](#vectorcode-deregister)
* [Debugging and Logging](#debugging-and-logging)

<!-- mtoc-end -->

## Installation
Using Lazy:

```lua 
{
  "Davidyz/VectorCode",
  version = "*", -- optional, depending on whether you're on nightly or release
  dependencies = { "nvim-lua/plenary.nvim" },
  cmd = "VectorCode", -- if you're lazy-loading VectorCode
}
```
The VectorCode CLI and neovim plugin share the same release scheme (version
numbers). In other words, CLI 0.1.3 is guaranteed to work with neovim plugin
0.1.3, but if you use CLI 0.1.0 with neovim plugin 0.1.3, they may not work
together because the neovim plugin is built for a newer CLI release and depends
on newer features/breaking changes.

To ensure maximum compatibility, please either:
1. Use release build for VectorCode CLI and pin to the releases for the
   neovim plugin;

**OR**

2. Use the latest commit for the neovim plugin with VectorCode installed from
   the latest GitHub commit.

It may be helpful to use a `build` hook to automatically upgrade the CLI when
the neovim plugin updates. For example, if you're using lazy.nvim and `uv`,
you can use the following plugin spec:

```lua
{
  "Davidyz/VectorCode",
  version = "*",
  build = "uv tool upgrade vectorcode", -- This helps keeping the CLI up-to-date
  -- build = "pipx upgrade vectorcode", -- If you used pipx to install the CLI
  dependencies = { "nvim-lua/plenary.nvim" },
}
```

> This plugin is developed and tested on neovim _v0.11_. It may work on older
> versions, but I do not test on them before publishing.

### Mason.nvim 

The VectorCode CLI and LSP server are available in `mason.nvim`. If you choose to
install the CLI through mason, you may need to pay extra attention to the version 
pinning because the package updates on mason usually takes extra time.

### Nix

There's a community-maintained [nix package](https://nixpk.gs/pr-tracker.html?pr=413395) 
submitted by [@sarahec](https://github.com/sarahec) for the Neovim plugin.

### Lazy Loading
When you call VectorCode APIs or integration interfaces as a part of another
plugin's configuration, it's important to make sure that VectorCode is loaded
BEFORE the plugin you're trying to use.

For example, in [lazy.nvim](https://github.com/folke/lazy.nvim), it's not
sufficient to simply add VectorCode as a dependency. You'd also need to wrap the 
`opts` table in a function:
```lua
{
  "olimorris/codecompanion.nvim",
  opts = function()
    return your_opts_here
  end
}
```
If you pass a table, instead of a function, as the value for the `opts` key,
neovim will try to load the VectorCode components immediately on startup
(potentially even before the plugin is added to the
[`rtp`](https://neovim.io/doc/user/options.html#'runtimepath')) and will cause
some errors.

## Integrations

VectorCode is a _library_ plugin that needs to be paired with some AI plugin to
assist your workflow. The core APIs are documented in the [API references](./api_references.md).
For some plugins, we provide built-in support that simplify the integrations.
You can read about the relevant sections below about the specific plugin that
you want to use VectorCode with.

If, unfortunately, your AI plugin of choice is not listed here, you can either
use the APIs listed in the [API references](./api_references.md) to build your
own integration interface, or open an issue (either in this repo or in the AI 
plugin's repo) to request for support.

Currently supported plugins:
- [milanglacier/minuet-ai.nvim](https://github.com/milanglacier/minuet-ai.nvim);
- [olimorris/codecompanion.nvim](https://github.com/olimorris/codecompanion.nvim);
- [CopilotC-Nvim/CopilotChat.nvim](https://github.com/CopilotC-Nvim/CopilotChat.nvim);
- [ravitemer/mcphub.nvim](https://github.com/ravitemer/mcphub.nvim);
- [nvim-lualine/lualine.nvim](https://github.com/nvim-lualine/lualine.nvim);
- [rebelot/heirline.nvim](https://github.com/rebelot/heirline.nvim).

### [milanglacier/minuet-ai.nvim](https://github.com/milanglacier/minuet-ai.nvim)

You can use the [aysnc caching API](./api_references.md#cached-asynchronous-api)
to include query results in the prompt. 

See
[minuet-ai documentation](https://github.com/milanglacier/minuet-ai.nvim/blob/main/recipes.md#integration-with-vectorcode)
and
[Prompt Gallery](https://github.com/Davidyz/VectorCode/wiki/Prompt-Gallery) for
instructions to modify the prompts to use VectorCode context for completion.

To control the number of results to be included in the prompt and some other
behaviour, you can either set the opts when calling the `register_buffer` function, 
or change the value of `async_opts.n_query` in the `setup` function 
(see [configuration](#configuration)).

### [olimorris/codecompanion.nvim](https://github.com/olimorris/codecompanion.nvim)

[![asciicast](https://asciinema.org/a/8WP8QJHNAR9lEllZSSx3poLPD.svg)](https://asciinema.org/a/8WP8QJHNAR9lEllZSSx3poLPD?t=3)

#### Tools
The following requires VectorCode 0.7+ and a recent version of CodeCompanion.nvim.

The CodeCompanion extension will register the following tools:
- `@{vectorcode_ls}`: an equivalent of `vectorcode ls` command that shows the
  indexed projects on your system;
- `@{vectorcode_query}`: an equivalent of `vectorcode query` command that
  searches from a project;
- `@{vectorcode_vectorise}`: an equivalent of `vectorcode vectorise` command
  that adds files to the database;
- `@{vectorcode_files_ls}`: an equivalent of `vectorcode files ls` command that
  gives a list of indexed files in a project;
- `@{vectorcode_files_rm}`: an equivalent of `vectorcode files rm` command that
  removes files from a collection.

By default, it'll also create a tool group called `@{vectorcode_toolbox}`, which
contains the `vectorcode_ls`, `vectorcode_query` and `vectorcode_vectorise`
tools. You can customise the members of this toolbox by the `include_in_toolbox`
option explained below.

```lua
---@module "vectorcode"
require("codecompanion").setup({
  extensions = {
    vectorcode = {
      ---@type VectorCode.CodeCompanion.ExtensionOpts
      opts = {
        tool_group = {
          -- this will register a tool group called `@vectorcode_toolbox` that contains all 3 tools
          enabled = true,
          -- a list of extra tools that you want to include in `@vectorcode_toolbox`.
          -- if you use @vectorcode_vectorise, it'll be very handy to include
          -- `file_search` here.
          extras = {},
          collapse = false, -- whether the individual tools should be shown in the chat
        },
        tool_opts = {
          ---@type VectorCode.CodeCompanion.ToolOpts
          ["*"] = {},
          ---@type VectorCode.CodeCompanion.LsToolOpts
          ls = {},
          ---@type VectorCode.CodeCompanion.VectoriseToolOpts
          vectorise = {},
          ---@type VectorCode.CodeCompanion.QueryToolOpts
          query = {
            max_num = { chunk = -1, document = -1 },
            default_num = { chunk = 50, document = 10 },
            include_stderr = false,
            use_lsp = false,
            no_duplicate = true,
            chunk_mode = false,
            ---@type VectorCode.CodeCompanion.SummariseOpts
            summarise = {
              ---@type boolean|(fun(chat: CodeCompanion.Chat, results: VectorCode.QueryResult[]):boolean)|nil
              enabled = false,
              adapter = nil,
              query_augmented = true,
            },
          },
          files_ls = {},
          files_rm = {},
        },
      },
    },
  },
})
```

The following are the common options that all tools supports:

- `use_lsp`: whether to use the LSP backend to run the queries. Using LSP
  provides some insignificant performance boost and a nice notification pop-up
  if you're using [fidget.nvim](https://github.com/j-hui/fidget.nvim). Default:
  `true` if `async_backend` is set to `"lsp"` in `setup()`. Otherwise, it'll be
  `false`;
- `requires_approval`: whether CodeCompanion.nvim asks for your approval before
  executing the tool call. Default: `false` for `ls` and `query`; `true` for
  `vectorise`;
- `include_in_toolbox`: whether this tool should be included in
  `vectorcode_toolbox`. Default: `true` for `query`, `vectorise` and `ls`,
  `false` for `files_*`.

In the `tool_opts` table, you may either configure these common options
individually, or use the `["*"]` key to specify the default settings for all
tools. If you've set both the default settings (via `["*"]`) and the individual
settings for a tool, the individual settings take precedence.

The `query` tool contains the following extra config options:
- `chunk_mode`: boolean, whether the VectorCode backend should return chunks or
  full documents. Default: `false`;
- `max_num` and `default_num`: If they're set to integers, they represent the
  default and maximum allowed number of results returned by VectorCode
  (regardless of  document or chunk mode). They can also be set to tables with 2
  keys: `document` and `chunk`. In this case, their values would be used for the
  corresponding mode. You may ask the LLM to request a different number of
  chunks or documents, but they'll be capped by the values in `max_num`.
  Default: See the sample snippet above. Negative values for `max_num` means
  unlimited.
- `no_duplicate`: boolean, whether the query calls should attempt to exclude files
  that has been retrieved and provided in the previous turns of the current chat.
  This helps saving tokens and increase the chance of retrieving the correct files
  when the previous retrievals fail to do so. Default: `true`.
- `summarise`: optional summarisation for the retrieval results. This is a table
  with the following keys:
  - `enabled`: This can either be a boolean that toggles summarisation on/off
    completely, or a function that accepts the `CodeCompanion.Chat` object and
    the raw query results as the 2 paramters and returns a boolean. When it's
    the later, it'll be evaluated for every tool call. This allows you to write
    some custom logic to dynamically turn summarisation on and off. _When the
    summarisation is enabled, but you find the summaries not informative enough,
    you can tell the LLM to disable the summarisation during the chat so that it
    sees the raw information_;
  - `adapter`: See [CodeCompanion documentation](https://codecompanion.olimorris.dev/configuration/adapters.html#configuring-adapters).
    When not provided, it'll use the chat adapter;
  - `system_prompt`: When set to a string, this will be used as the system
    prompt for the summarisation model. When set to a function, it'll be called
    with the default system prompt as the only parameter, and it should return
    a string that will be used as a system prompt. This allows you to
    append/prepend things to the default system prompt;
  - `query_augmented`: boolean, whether the system prompt should contain the
    query so that when the LLM decide what information to include, it _may_ be
    able to avoid omitting stuff related to query.

#### Prompt Library

On VectorCode 0.7.16+ and CodeCompanion.nvim 17.20.0+, VectorCode also provides a 
customisable prompt library that helps you RAG local directories. The presets 
provided by VectorCode are available 
[here](../../lua/vectorcode/integrations/codecompanion/prompts/presets.lua), which 
you can refer to if you wish to build local RAG APPs with CodeCompanion.nvim and 
VectorCode.

```lua 
require("codecompanion").setup({
  extensions = {
    vectorcode = {
      ---@type VectorCode.CodeCompanion.ExtensionOpts
      opts = {
        ---@type table<string, VectorCode.CodeCompanion.PromptFactory.Opts>
        prompt_library = {
          {
            ["Neovim Tutor"] = {
              -- this is for demonstration only.
              -- "Neovim Tutor" is shipped with this plugin already,
              -- and you don't need to add it in the config
              -- unless you're not happy with the defaults.
              project_root = vim.env.VIMRUNTIME,
              file_patterns = { "lua/**/*.lua", "doc/**/*.txt" },
              -- system_prompt = ...,
              -- user_prompt = ...,
            },
          },
        },
      },
    },
  },
})
```

The `prompt_library` option is a mapping of prompt name (`string`) to a lua table 
(type annotation available) that contains some information used to generate the 
embeddings:

- `project_root`: `string`, the path to the directory (for example, 
  `/usr/share/nvim/runtime/`);
- `file_patterns`: `string[]`, file name patterns that defines files to be vectorised. 
  You should either use absolute paths or relative paths from the project root;
- `system_prompt` and `user_prompt`: `string|fun(context:table):string|nil`: 
  These options allow you to customise the prompts. See 
  [codecompanion.nvim documentation](https://codecompanion.olimorris.dev/extending/prompts#recipe-2-using-context-in-your-prompts)
  if you want to use a function here that build the prompts from the context.

The first time will take some extra time for computing the embeddings, but the 
subsequent runs should be a lot faster.

### [CopilotC-Nvim/CopilotChat.nvim](https://github.com/CopilotC-Nvim/CopilotChat.nvim)

[CopilotC-Nvim/CopilotChat.nvim](https://github.com/CopilotC-Nvim/CopilotChat.nvim) 
is a Neovim plugin that provides an interface to GitHub Copilot Chat. VectorCode 
integration enriches the conversations by providing relevant repository context.

#### Setup

VectorCode offers a dedicated integration with CopilotChat.nvim that provides 
contextual information about your codebase to enhance Copilot's responses. Add this 
to your CopilotChat configuration:

```lua
local vectorcode_ctx =
  require("vectorcode.integrations.copilotchat").make_context_provider({
    prompt_header = "Here are relevant files from the repository:", -- Customize header text
    prompt_footer = "\nConsider this context when answering:", -- Customize footer text
    skip_empty = true, -- Skip adding context when no files are retrieved
  })

require("CopilotChat").setup({
  -- Your other CopilotChat options...

  contexts = {
    -- Add the VectorCode context provider
    vectorcode = vectorcode_ctx,
  },

  -- Enable VectorCode context in your prompts
  prompts = {
    Explain = {
      prompt = "Explain the following code in detail:\n$input",
      context = { "selection", "vectorcode" }, -- Add vectorcode to the context
    },
    -- Other prompts...
  },
})
```

#### Configuration Options

The `make_context_provider` function accepts these options:

- `prompt_header`: Text that appears before the code context (default: "The following are relevant files from the repository. Use them as extra context for helping with code completion and understanding:")
- `prompt_footer`: Text that appears after the code context (default: "\nExplain and provide a strategy with examples about: \n")
- `skip_empty`: Whether to skip adding context when no files are retrieved (default: true)
- `format_file`: A function that formats each retrieved file (takes a file result object and returns formatted string)

#### Usage Tips

1. Register your buffers with VectorCode (`:VectorCode register`) to enable context fetching
2. Create different prompt templates with or without VectorCode context depending on your needs
3. For large codebases, consider adjusting the number of retrieved documents using `n_query` when registering buffers

#### Performance Optimization

The integration includes caching to avoid sending duplicate context to the LLM, which helps reduce token usage when asking multiple questions about the same codebase.

#### Using with Sticky Prompts

You can configure VectorCode to be part of your sticky prompts, ensuring every conversation includes relevant codebase context automatically:

```lua
require("CopilotChat").setup({
  -- Your other CopilotChat options...

  sticky = {
    "Using the model $claude-3.7-sonnet-thought",
    "#vectorcode", -- Automatically includes repository context in every conversation
  },
})
```

This configuration will include both the model specification and repository context in every conversation with CopilotChat.

---
### Status Line Component

#### [nvim-lualine/lualine.nvim](https://github.com/nvim-lualine/lualine.nvim)
A `lualine` component that shows the status of the async job and the number of
cached retrieval results.
```lua
tabline = {
  lualine_y = {
    require("vectorcode.integrations").lualine(opts),
  },
}
```
`opts` is a table with the following configuration option:
- `show_job_count`: boolean, whether to show the number of running jobs for the
  buffer. Default: `false`.

This will, however, start VectorCode when lualine starts (which usually means
when neovim starts). If this bothers you, you can use the following
snippet:
```lua
tabline = {
  lualine_y = {
    {
      function()
        return require("vectorcode.integrations").lualine(opts)[1]()
      end,
      cond = function()
        if package.loaded["vectorcode"] == nil then
          return false
        else
          return require("vectorcode.integrations").lualine(opts).cond()
        end
      end,
    },
  },
}
```
This will further delay the loading of VectorCode to the moment you (or one of
your plugins that actually retrieves context from VectorCode) load VectorCode.

#### [heirline.nvim](https://github.com/rebelot/heirline.nvim)

A heirline component is available as:
```lua
local vectorcode_component = require("vectorcode.integrations").heirline({
  show_job_count = true,
  component_opts = {
    -- put other field of the components here.
    -- they'll be merged into the final component.
  },
})
```

### [fidget.nvim](https://github.com/j-hui/fidget.nvim)

If you're using
[a LSP backend](https://github.com/Davidyz/VectorCode/blob/main/docs/cli.md#lsp-mode),
there will be a notification when there's a pending request for queries. As long
as the LSP backend is working, no special configuration is needed for this.

### Model Context Protocol (MCP)

The Python package contains an optional `mcp` dependency group. After installing
this, you can use the MCP server with any MCP client. For example, to use it
with [mcphub.nvim](https://github.com/ravitemer/mcphub.nvim), simply add this
server in the JSON config:
```json
{
  "mcpServers": {
    "vectorcode-mcp-server": {
      "command": "vectorcode-mcp-server",
      "args": []
    }
  }
}
```

## Configuration

### `setup(opts?)`

This function controls the behaviour of some of the APIs provided by the
VectorCode neovim plugin. If you're using built-in integration interfaces, you
usually don't have to worry about this section, unless otherwise specified in
the relevant section.

This function initialises the VectorCode client and sets up some default

```lua
-- Default configuration
require("vectorcode").setup(
  ---@type VectorCode.Opts
  {
    cli_cmds = {
      vectorcode = "vectorcode",
    },
    ---@type VectorCode.RegisterOpts
    async_opts = {
      debounce = 10,
      events = { "BufWritePost", "InsertEnter", "BufReadPost" },
      exclude_this = true,
      n_query = 1,
      notify = false,
      query_cb = require("vectorcode.utils").make_surrounding_lines_cb(-1),
      run_on_register = false,
    },
    async_backend = "default", -- or "lsp"
    exclude_this = true,
    n_query = 1,
    notify = true,
    timeout_ms = 5000,
    on_setup = {
      update = false, -- set to true to enable update when `setup` is called.
      lsp = false,
    },
    sync_log_env_var = false,
  }
)
```

The following are the available options for the parameter of this function:
- `cli_cmds`: A table to customize the CLI command names / paths used by the plugin.
  Supported key:
  - `vectorcode`: The command / path to use for the main CLI tool. Default: `"vectorcode"`.
- `n_query`: number of retrieved documents. A large number gives a higher chance
  of including the right file, but with the risk of saturating the context 
  window and getting truncated. Default: `1`;
- `notify`: whether to show notifications when a query is completed.
  Default: `true`;
- `timeout_ms`: timeout in milliseconds for the query operation. Applies to
  synchronous API only. Default: 
  `5000` (5 seconds);
- `exclude_this`: whether to exclude the file you're editing. Setting this to
  `false` may lead to an outdated version of the current file being sent to the
  LLM as the prompt, and can lead to generations with outdated information;
- `async_opts`: default options used when registering buffers. See 
  [`register_buffer(bufnr?, opts?)`](#register_bufferbufnr-opts) for details;
- `async_backend`: the async backend to use, currently either `"default"` or
  `"lsp"`. Default: `"default"`;
- `on_setup`: some actions that can be registered to run when `setup` is called.
  Supported keys:
  - `update`: if `true`, the plugin will run `vectorcode update` on startup to
    update the embeddings;
  - `lsp`: if `true`, the plugin will try to start the LSP server on startup so
    that you won't need to wait for the server loading when making your first 
    request. _Please pay extra attention on lazy-loading so that the LSP server
    won't be started without a buffer to be attached to (see [here](https://github.com/Davidyz/VectorCode/pull/234))._
- `sync_log_env_var`: `boolean`. If true, this plugin will automatically set the
  `VECTORCODE_LOG_LEVEL` environment variable for LSP or cmd processes started
  within your neovim session when logging is turned on for this plugin. Use at 
  caution because the non-LSP CLI write all logs to stderr, which _may_ make this plugin 
  VERY verbose. See [Debugging and Logging](#debugging-and-logging) for details
  on how to turn on logging.

You may notice that a lot of options in `async_opts` are the same as the other
options in the top-level of the main option table. This is because the top-level
options are designated for the [Synchronous API](#synchronous-api) and the ones
in `async_opts` is for the [Cached Asynchronous API](#cached-asynchronous-api).
The `async_opts` will reuse the synchronous API options if not explicitly
configured.

## User Command

The neovim plugin provides user commands to work with [async caching](#cached-asynchronous-api).

### `VectorCode register`

Register the current buffer for async caching. It's possible to register the
current buffer to a different vectorcode project by passing the `project_root`
parameter:
```
:VectorCode register project_root=path/to/another/project/
```
This is useful if you're working on a project that is closely related to a
different project, for example a utility repository for a main library or a
documentation repository. Alternatively, you can call the [lua API](#cached-asynchronous-api) in an autocmd:
```lua
vim.api.nvim_create_autocmd("LspAttach", {
  callback = function()
    local bufnr = vim.api.nvim_get_current_buf()
    cacher.async_check("config", function()
      cacher.register_buffer(bufnr, {
        n_query = 10,
      })
    end, nil)
  end,
  desc = "Register buffer for VectorCode",
})
```
The latter avoids the manual registrations, but registering too many buffers
means there will be a lot of background processes/requests being sent to
VectorCode. Choose these based on your workflow and the capability of your
system.

### `VectorCode deregister`

Deregister the current buffer. Any running jobs will be killed, cached results
will be deleted, and no more queries will be run.


## Debugging and Logging

You can enable logging by setting `VECTORCODE_NVIM_LOG_LEVEL` environment
variable to a 
[supported log level](https://github.com/nvim-lua/plenary.nvim/blob/857c5ac632080dba10aae49dba902ce3abf91b35/lua/plenary/log.lua#L44). 
The log file will be written to `stdpath("log")` or `stdpath("cache")`. On
Linux, this is usually `~/.local/state/nvim/`.
