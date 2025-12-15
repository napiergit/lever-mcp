/**
 * OAuth configuration for Gmail integration.
 * Supports both FastMCP OAuth proxy and direct OAuth 2.0 on-behalf-of flows.
 */
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Gmail API scopes
export const GMAIL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.compose'
];

export interface TokenData {
    token?: string;
    refresh_token?: string;
    token_uri?: string;
    client_id?: string;
    client_secret?: string;
    scopes?: string[];
    access_token?: string;
    expires_in?: number;
    token_type?: string;
    scope?: string;
}

export class OAuthConfig {
    public readonly clientId: string | undefined;
    public readonly clientSecret: string | undefined;
    public readonly redirectUri: string;
    public readonly tokenStoragePath: string;

    constructor() {
        this.clientId = process.env.GOOGLE_CLIENT_ID;
        this.clientSecret = process.env.GOOGLE_CLIENT_SECRET;
        // Construct redirect URI from MCP_SERVER_BASE_URL
        const baseUrl = process.env.MCP_SERVER_BASE_URL || 'https://isolated-coffee-reindeer.fastmcp.app';
        this.redirectUri = `${baseUrl}/oauth/callback`;
        this.tokenStoragePath = process.env.TOKEN_STORAGE_PATH || './.oauth_tokens';
    }

    isConfigured(): boolean {
        return Boolean(this.clientId && this.clientSecret);
    }

    getClientConfig(): any {
        if (!this.isConfigured()) {
            throw new Error(
                'OAuth not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET ' +
                'environment variables.'
            );
        }

        return {
            installed: {
                client_id: this.clientId,
                client_secret: this.clientSecret,
                redirect_uris: [this.redirectUri],
                auth_uri: 'https://accounts.google.com/o/oauth2/auth',
                token_uri: 'https://oauth2.googleapis.com/token',
                auth_provider_x509_cert_url: 'https://www.googleapis.com/oauth2/v1/certs'
            }
        };
    }

    async saveToken(tokenData: TokenData, userId: string = 'default'): Promise<void> {
        try {
            await fs.mkdir(this.tokenStoragePath, { recursive: true });
            const tokenFile = path.join(this.tokenStoragePath, `${userId}_token.json`);
            
            await fs.writeFile(tokenFile, JSON.stringify(tokenData, null, 2));
            
            console.log(`Token saved for user: ${userId}`);
        } catch (error: any) {
            // Read-only filesystem (common in serverless/cloud deployments)
            // This is OK - tokens should be managed by the MCP client (on-behalf-of flow)
            console.warn(`Cannot save token to filesystem (read-only): ${error.message}`);
            console.log('Token storage skipped - using on-behalf-of flow where client manages tokens');
        }
    }

    async loadToken(userId: string = 'default'): Promise<TokenData | null> {
        try {
            const tokenFile = path.join(this.tokenStoragePath, `${userId}_token.json`);
            
            try {
                await fs.access(tokenFile);
            } catch {
                return null;
            }
            
            const data = await fs.readFile(tokenFile, 'utf8');
            return JSON.parse(data);
        } catch (error: any) {
            // Read-only filesystem - no tokens stored locally
            console.debug(`Cannot load token from filesystem: ${error.message}`);
            return null;
        }
    }

    async deleteToken(userId: string = 'default'): Promise<void> {
        try {
            const tokenFile = path.join(this.tokenStoragePath, `${userId}_token.json`);
            
            try {
                await fs.access(tokenFile);
                await fs.unlink(tokenFile);
                console.log(`Token deleted for user: ${userId}`);
            } catch {
                // File doesn't exist or can't be deleted
            }
        } catch (error: any) {
            // Read-only filesystem - nothing to delete
            console.debug(`Cannot delete token from filesystem: ${error.message}`);
        }
    }
}

// Global config instance
export const oauthConfig = new OAuthConfig();
