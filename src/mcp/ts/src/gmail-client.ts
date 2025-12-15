/**
 * Gmail client with OAuth 2.0 support.
 * Handles authentication and email sending via Gmail API.
 */
import { google } from 'googleapis';
import { OAuth2Client } from 'google-auth-library';
import { oauthConfig, GMAIL_SCOPES, TokenData } from './oauth-config.js';

export interface EmailOptions {
    to: string;
    subject: string;
    body: string;
    cc?: string;
    bcc?: string;
    isHtml?: boolean;
}

export interface EmailResult {
    status: string;
    messageId: string;
    to: string;
    subject: string;
}

export class GmailClient {
    private userId: string;
    private oauth2Client: OAuth2Client | null = null;

    constructor(accessToken?: string, userId: string = 'default') {
        this.userId = userId;

        if (accessToken) {
            // Use token provided by agent (on-behalf-of flow)
            this.oauth2Client = new OAuth2Client(
                oauthConfig.clientId,
                oauthConfig.clientSecret,
                oauthConfig.redirectUri
            );
            this.oauth2Client.setCredentials({
                access_token: accessToken,
                scope: GMAIL_SCOPES.join(' ')
            });
        } else {
            // Try to load stored token
            this.loadCredentials();
        }
    }

    private async loadCredentials(): Promise<void> {
        const tokenData = await oauthConfig.loadToken(this.userId);

        if (tokenData) {
            this.oauth2Client = new OAuth2Client(
                oauthConfig.clientId,
                oauthConfig.clientSecret,
                oauthConfig.redirectUri
            );

            this.oauth2Client.setCredentials({
                access_token: tokenData.access_token || tokenData.token,
                refresh_token: tokenData.refresh_token,
                scope: GMAIL_SCOPES.join(' ')
            });

            // Refresh token if needed
            try {
                const { credentials } = await this.oauth2Client.refreshAccessToken();
                this.oauth2Client.setCredentials(credentials);
                
                // Save refreshed token
                await this.saveCredentials(credentials);
                console.log('Token refreshed successfully');
            } catch (error) {
                console.error('Failed to refresh token:', error);
                this.oauth2Client = null;
            }
        }
    }

    private async saveCredentials(credentials: any): Promise<void> {
        if (this.oauth2Client && credentials) {
            const tokenData: TokenData = {
                access_token: credentials.access_token,
                refresh_token: credentials.refresh_token,
                token_uri: credentials.token_uri,
                client_id: oauthConfig.clientId,
                client_secret: oauthConfig.clientSecret,
                scopes: GMAIL_SCOPES
            };
            await oauthConfig.saveToken(tokenData, this.userId);
        }
    }

    isAuthenticated(): boolean {
        return this.oauth2Client !== null && Boolean(this.oauth2Client.credentials.access_token);
    }

    async setToken(tokenData: TokenData | string): Promise<void> {
        if (typeof tokenData === 'string') {
            // Simple access token string
            this.oauth2Client = new OAuth2Client(
                oauthConfig.clientId,
                oauthConfig.clientSecret,
                oauthConfig.redirectUri
            );
            this.oauth2Client.setCredentials({
                access_token: tokenData,
                scope: GMAIL_SCOPES.join(' ')
            });
        } else if (typeof tokenData === 'object' && tokenData !== null) {
            // Full token data
            if (tokenData.access_token) {
                this.oauth2Client = new OAuth2Client(
                    tokenData.client_id || oauthConfig.clientId,
                    tokenData.client_secret || oauthConfig.clientSecret,
                    oauthConfig.redirectUri
                );
                this.oauth2Client.setCredentials({
                    access_token: tokenData.access_token,
                    refresh_token: tokenData.refresh_token,
                    scope: GMAIL_SCOPES.join(' ')
                });
                // Save for future use
                await this.saveCredentials(this.oauth2Client.credentials);
            } else {
                throw new Error("Token data must contain 'access_token'");
            }
        } else {
            throw new Error('Token must be a string or object');
        }
    }

    async sendEmail(options: EmailOptions): Promise<EmailResult> {
        if (!this.isAuthenticated()) {
            throw new Error(
                'Not authenticated. Please provide an OAuth token or complete authentication flow.'
            );
        }

        try {
            // Build Gmail service
            const gmail = google.gmail({ version: 'v1', auth: this.oauth2Client! });

            // Create message
            const messageParts = [
                `To: ${options.to}`,
                `Subject: ${options.subject}`,
                'MIME-Version: 1.0',
            ];

            if (options.isHtml !== false) {
                messageParts.push('Content-Type: text/html; charset=utf-8');
            } else {
                messageParts.push('Content-Type: text/plain; charset=utf-8');
            }

            if (options.cc) {
                messageParts.push(`Cc: ${options.cc}`);
            }
            if (options.bcc) {
                messageParts.push(`Bcc: ${options.bcc}`);
            }

            messageParts.push(''); // Empty line between headers and body
            messageParts.push(options.body);

            const rawMessage = messageParts.join('\n');

            // Encode message
            const encodedMessage = Buffer.from(rawMessage, 'utf-8')
                .toString('base64')
                .replace(/\+/g, '-')
                .replace(/\//g, '_')
                .replace(/=+$/, '');

            // Send message
            const response = await gmail.users.messages.send({
                userId: 'me',
                requestBody: {
                    raw: encodedMessage
                }
            });

            console.log(`Email sent successfully. Message ID: ${response.data.id}`);

            return {
                status: 'success',
                messageId: response.data.id || '',
                to: options.to,
                subject: options.subject
            };

        } catch (error: any) {
            console.error('Gmail API error:', error);
            throw error;
        }
    }

    getAuthUrl(): string {
        if (!oauthConfig.isConfigured()) {
            throw new Error('OAuth not configured');
        }

        const oauth2Client = new OAuth2Client(
            oauthConfig.clientId,
            oauthConfig.clientSecret,
            oauthConfig.redirectUri
        );

        const authUrl = oauth2Client.generateAuthUrl({
            access_type: 'offline',
            scope: GMAIL_SCOPES,
            include_granted_scopes: true,
            prompt: 'consent'
        });

        return authUrl;
    }

    async exchangeCodeForToken(code: string): Promise<TokenData> {
        if (!oauthConfig.isConfigured()) {
            throw new Error('OAuth not configured');
        }

        const oauth2Client = new OAuth2Client(
            oauthConfig.clientId,
            oauthConfig.clientSecret,
            oauthConfig.redirectUri
        );

        const { tokens } = await oauth2Client.getToken(code);
        
        this.oauth2Client = oauth2Client;
        this.oauth2Client.setCredentials(tokens);
        await this.saveCredentials(tokens);

        return {
            access_token: tokens.access_token || undefined,
            refresh_token: tokens.refresh_token || undefined,
            expires_in: tokens.expiry_date ? Math.floor((tokens.expiry_date - Date.now()) / 1000) : undefined,
            token_type: tokens.token_type || 'Bearer',
            scope: tokens.scope
        };
    }
}
