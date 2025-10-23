/**API Key Validation - Test API keys before saving*/

export type ProviderType = 'claude-code' | 'anthropic' | 'openrouter' | 'openai';

export interface ValidationResult {
  valid: boolean;
  error?: string;
  provider?: string;
  quotaExceeded?: boolean;
  rateLimited?: boolean;
}

class APIKeyValidator {
  /**
   * Validate an API key for a given provider
   */
  async validateKey(provider: ProviderType, apiKey: string): Promise<ValidationResult> {
    if (!apiKey || apiKey.trim().length === 0) {
      return {
        valid: false,
        error: 'API key cannot be empty'
      };
    }

    switch (provider) {
      case 'anthropic':
        return this.validateAnthropicKey(apiKey);
      case 'openai':
        return this.validateOpenAIKey(apiKey);
      case 'openrouter':
        return this.validateOpenRouterKey(apiKey);
      case 'claude-code':
        return this.validateClaudeCodeKey(apiKey);
      default:
        return {
          valid: false,
          error: 'Unknown provider'
        };
    }
  }

  /**
   * Validate Anthropic API key
   */
  private async validateAnthropicKey(apiKey: string): Promise<ValidationResult> {
    try {
      const response = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
          'anthropic-version': '2023-06-01',
          'x-api-key': apiKey,
          'content-type': 'application/json'
        },
        body: JSON.stringify({
          model: 'claude-3-5-sonnet-20241022',
          max_tokens: 1,
          messages: [
            { role: 'user', content: 'test' }
          ]
        })
      });

      if (response.status === 200 || response.status === 400) {
        // 200 = success, 400 = valid key but bad request (still means key works)
        return { valid: true, provider: 'anthropic' };
      } else if (response.status === 401) {
        return { valid: false, error: 'Invalid API key' };
      } else if (response.status === 429) {
        return { valid: true, provider: 'anthropic', rateLimited: true };
      } else if (response.status === 402) {
        return { valid: true, provider: 'anthropic', quotaExceeded: true };
      } else {
        const errorText = await response.text();
        return { valid: false, error: `Validation failed: ${errorText}` };
      }
    } catch (error) {
      return {
        valid: false,
        error: `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`
      };
    }
  }

  /**
   * Validate OpenAI API key
   */
  private async validateOpenAIKey(apiKey: string): Promise<ValidationResult> {
    try {
      const response = await fetch('https://api.openai.com/v1/models', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${apiKey}`
        }
      });

      if (response.status === 200) {
        return { valid: true, provider: 'openai' };
      } else if (response.status === 401) {
        return { valid: false, error: 'Invalid API key' };
      } else if (response.status === 429) {
        return { valid: true, provider: 'openai', rateLimited: true };
      } else if (response.status === 402 || response.status === 403) {
        return { valid: true, provider: 'openai', quotaExceeded: true };
      } else {
        const errorText = await response.text();
        return { valid: false, error: `Validation failed: ${errorText}` };
      }
    } catch (error) {
      return {
        valid: false,
        error: `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`
      };
    }
  }

  /**
   * Validate OpenRouter API key
   */
  private async validateOpenRouterKey(apiKey: string): Promise<ValidationResult> {
    try {
      const response = await fetch('https://openrouter.ai/api/v1/auth/key', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${apiKey}`
        }
      });

      if (response.status === 200) {
        return { valid: true, provider: 'openrouter' };
      } else if (response.status === 401) {
        return { valid: false, error: 'Invalid API key' };
      } else if (response.status === 429) {
        return { valid: true, provider: 'openrouter', rateLimited: true };
      } else {
        const errorText = await response.text();
        return { valid: false, error: `Validation failed: ${errorText}` };
      }
    } catch (error) {
      return {
        valid: false,
        error: `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`
      };
    }
  }

  /**
   * Validate Claude Code (just check format since it uses Anthropic keys)
   */
  private async validateClaudeCodeKey(apiKey: string): Promise<ValidationResult> {
    // Claude Code uses Anthropic API keys
    // Just validate the format for now
    if (apiKey.startsWith('sk-ant-')) {
      // Could optionally test against Anthropic API
      return this.validateAnthropicKey(apiKey);
    } else {
      return {
        valid: false,
        error: 'Claude Code requires an Anthropic API key (starts with sk-ant-)'
      };
    }
  }

  /**
   * Get validation status message
   */
  getStatusMessage(result: ValidationResult): string {
    if (result.valid) {
      if (result.quotaExceeded) {
        return '⚠️ Valid key but quota exceeded';
      } else if (result.rateLimited) {
        return '⚠️ Valid key but rate limited';
      } else {
        return '✅ Valid API key';
      }
    } else {
      return `❌ ${result.error || 'Invalid API key'}`;
    }
  }

  /**
   * Get status color for UI
   */
  getStatusColor(result: ValidationResult): 'success' | 'warning' | 'error' {
    if (result.valid) {
      if (result.quotaExceeded || result.rateLimited) {
        return 'warning';
      }
      return 'success';
    }
    return 'error';
  }
}

// Export singleton instance
export const apiKeyValidator = new APIKeyValidator();
