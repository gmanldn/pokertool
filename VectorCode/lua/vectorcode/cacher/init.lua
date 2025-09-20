local vc_config = require("vectorcode.config")
local jobrunner = require("vectorcode.jobrunner.cmd")

return {
  lsp = require("vectorcode.cacher.lsp"),
  default = require("vectorcode.cacher.default"),
  utils = {
    ---Checks if VectorCode has been configured properly for your project.
    ---See the CLI manual for details.
    ---@param check_item string?
    ---@param on_success fun(out: vim.SystemCompleted)?
    ---@param on_failure fun(out: vim.SystemCompleted?)?
    async_check = function(check_item, on_success, on_failure)
      if not vc_config.has_cli() then
        if on_failure ~= nil then
          on_failure()
        end
        return
      end
      check_item = check_item or "config"
      jobrunner.run_async({ "check", check_item }, function(result, error, code, signal)
        local out = {
          stdout = table.concat(vim.iter(result):flatten(math.huge):totable()),
          stderr = table.concat(vim.iter(error):flatten(math.huge):totable()),
          code = code,
          signal = signal,
        }
        if out.code == 0 and type(on_success) == "function" then
          vim.schedule_wrap(on_success)(out)
        elseif out.code ~= 0 and type(on_failure) == "function" then
          vim.schedule_wrap(on_failure)(out)
        end
      end, 0)
    end,
  },
}
