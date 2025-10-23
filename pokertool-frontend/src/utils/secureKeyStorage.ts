/**Secure Key Storage - Encrypt API keys using Web Crypto API*/

interface EncryptedData {
  iv: string;
  encrypted: string;
}

class SecureKeyStorage {
  private static readonly STORAGE_PREFIX = 'encrypted_key_';
  private static readonly SALT_KEY = 'key_encryption_salt';

  /**
   * Generate or retrieve encryption key from Web Crypto API
   */
  private async getEncryptionKey(): Promise<CryptoKey> {
    // Get or create salt
    let salt = localStorage.getItem(SecureKeyStorage.SALT_KEY);
    if (!salt) {
      const saltArray = crypto.getRandomValues(new Uint8Array(16));
      salt = Array.from(saltArray).map(b => b.toString(16).padStart(2, '0')).join('');
      localStorage.setItem(SecureKeyStorage.SALT_KEY, salt);
    }

    // Convert salt to array
    const saltArray = new Uint8Array(
      salt.match(/.{2}/g)!.map(byte => parseInt(byte, 16))
    );

    // Generate key from password + salt
    const password = await this.getDevicePassword();
    const passwordKey = await crypto.subtle.importKey(
      'raw',
      new TextEncoder().encode(password),
      'PBKDF2',
      false,
      ['deriveBits', 'deriveKey']
    );

    return crypto.subtle.deriveKey(
      {
        name: 'PBKDF2',
        salt: saltArray,
        iterations: 100000,
        hash: 'SHA-256'
      },
      passwordKey,
      { name: 'AES-GCM', length: 256 },
      false,
      ['encrypt', 'decrypt']
    );
  }

  /**
   * Get device-specific password (not truly secure, but better than plaintext)
   */
  private async getDevicePassword(): Promise<string> {
    // Combine various browser/device identifiers
    const userAgent = navigator.userAgent;
    const language = navigator.language;
    const platform = navigator.platform;
    const vendor = navigator.vendor || '';

    // Create a somewhat unique device fingerprint
    return `${userAgent}|${language}|${platform}|${vendor}`;
  }

  /**
   * Encrypt and store an API key
   */
  async setKey(provider: string, key: string): Promise<void> {
    if (!key) {
      throw new Error('API key cannot be empty');
    }

    try {
      const encryptionKey = await this.getEncryptionKey();
      const iv = crypto.getRandomValues(new Uint8Array(12));

      const encrypted = await crypto.subtle.encrypt(
        { name: 'AES-GCM', iv },
        encryptionKey,
        new TextEncoder().encode(key)
      );

      const encryptedData: EncryptedData = {
        iv: Array.from(iv).map(b => b.toString(16).padStart(2, '0')).join(''),
        encrypted: Array.from(new Uint8Array(encrypted))
          .map(b => b.toString(16).padStart(2, '0'))
          .join('')
      };

      localStorage.setItem(
        `${SecureKeyStorage.STORAGE_PREFIX}${provider}`,
        JSON.stringify(encryptedData)
      );
    } catch (error) {
      console.error('Failed to encrypt API key:', error);
      throw new Error('Failed to securely store API key');
    }
  }

  /**
   * Retrieve and decrypt an API key
   */
  async getKey(provider: string): Promise<string | null> {
    try {
      const stored = localStorage.getItem(`${SecureKeyStorage.STORAGE_PREFIX}${provider}`);
      if (!stored) {
        return null;
      }

      const encryptedData: EncryptedData = JSON.parse(stored);
      const encryptionKey = await this.getEncryptionKey();

      const iv = new Uint8Array(
        encryptedData.iv.match(/.{2}/g)!.map(byte => parseInt(byte, 16))
      );

      const encrypted = new Uint8Array(
        encryptedData.encrypted.match(/.{2}/g)!.map(byte => parseInt(byte, 16))
      );

      const decrypted = await crypto.subtle.decrypt(
        { name: 'AES-GCM', iv },
        encryptionKey,
        encrypted
      );

      return new TextDecoder().decode(decrypted);
    } catch (error) {
      console.error('Failed to decrypt API key:', error);
      return null;
    }
  }

  /**
   * Remove a stored API key
   */
  removeKey(provider: string): void {
    localStorage.removeItem(`${SecureKeyStorage.STORAGE_PREFIX}${provider}`);
  }

  /**
   * Get all providers with stored keys
   */
  getStoredProviders(): string[] {
    const providers: string[] = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key?.startsWith(SecureKeyStorage.STORAGE_PREFIX)) {
        providers.push(key.substring(SecureKeyStorage.STORAGE_PREFIX.length));
      }
    }
    return providers;
  }

  /**
   * Clear all stored keys
   */
  clearAll(): void {
    const providers = this.getStoredProviders();
    providers.forEach(provider => this.removeKey(provider));
  }

  /**
   * Check if a key exists for a provider
   */
  hasKey(provider: string): boolean {
    return localStorage.getItem(`${SecureKeyStorage.STORAGE_PREFIX}${provider}`) !== null;
  }
}

// Export singleton instance
export const secureKeyStorage = new SecureKeyStorage();

// Export types
export type { EncryptedData };
