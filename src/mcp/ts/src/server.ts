/**
 * TypeScript MCP Server for Lever integration with Gmail
 * Ported from Python version with same functionality
 */
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
    CallToolRequestSchema,
    ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import express from 'express';
import { v4 as uuidv4 } from 'uuid';
import { LeverClient } from './client.js';
import { GmailClient } from './gmail-client.js';
import { oauthConfig, GMAIL_SCOPES } from './oauth-config.js';
import { EMAIL_TEMPLATES } from './email-templates.js';

// Configure logging
console.log('Starting Lever MCP TypeScript Server');

// In-memory storage for OAuth sessions (browser agents)
// Structure: {session_id: {"code": string, "timestamp": Date, "state": string}}
const oauthSessions = new Map<string, { code: string; timestamp: Date; state: string }>();

// MCP Server setup
const server = new Server(
    {
        name: 'lever-mcp-ts',
        version: '1.0.0',
    },
    {
        capabilities: {
            tools: {},
        },
    }
);

// Helper functions
async function listCandidates(limit: number = 10, offset?: string): Promise<string> {
    console.log(`Listing candidates with limit=${limit}, offset=${offset}`);
    try {
        const client = new LeverClient();
        const result = await client.getCandidates(limit, offset);
        return JSON.stringify(result, null, 2);
    } catch (error: any) {
        if (error.message.includes('LEVER_API_KEY')) {
            console.error(`Configuration error: ${error.message}`);
            return `Configuration error: ${error.message}`;
        }
        console.error(`Error listing candidates: ${error.message}`);
        return `Error listing candidates: ${error.message}`;
    }
}

async function getCandidate(candidateId: string): Promise<string> {
    console.log(`Getting candidate with id=${candidateId}`);
    try {
        const client = new LeverClient();
        const result = await client.getCandidate(candidateId);
        return JSON.stringify(result, null, 2);
    } catch (error: any) {
        if (error.message.includes('LEVER_API_KEY')) {
            console.error(`Configuration error: ${error.message}`);
            return `Configuration error: ${error.message}`;
        }
        console.error(`Error getting candidate: ${error.message}`);
        return `Error getting candidate: ${error.message}`;
    }
}

async function createRequisition(
    name: string,
    business: string,
    currentStatus: string,
    globalGrade: string,
    headcountTotal: number,
    hrbp: string,
    jobProgress: string,
    lastweekStatus: string,
    location: string,
    recruiter: string,
    requisitionCode: string,
    team: string
): Promise<string> {
    console.log(`Creating requisition: name=${name}, location=${location}, team=${team}`);
    try {
        const client = new LeverClient();
        const data = {
            name,
            business,
            current_status: currentStatus,
            global_grade: globalGrade,
            headcountTotal,
            hrbp,
            job_progress: jobProgress,
            lastweek_status: lastweekStatus,
            location,
            recruiter,
            requisitionCode,
            team
        };
        const result = await client.createRequisition(data);
        return JSON.stringify(result, null, 2);
    } catch (error: any) {
        if (error.message.includes('LEVER_API_KEY')) {
            console.error(`Configuration error: ${error.message}`);
            return `Configuration error: ${error.message}`;
        }
        console.error(`Error creating requisition: ${error.message}`);
        return `Error creating requisition: ${error.message}`;
    }
}

async function sendEmail(
    to: string,
    theme: string,
    subject?: string,
    cc?: string,
    bcc?: string,
    accessToken?: string,
    userId: string = 'default'
): Promise<string> {
    console.log(`Generating themed email: to=${to}, theme=${theme}, hasToken=${Boolean(accessToken)}`);

    // Get the template or default to birthday
    const template = EMAIL_TEMPLATES[theme.toLowerCase()] || EMAIL_TEMPLATES['birthday'];
    
    // Use provided subject or template subject
    const emailSubject = subject || template.subject;
    const emailBody = template.body;
    
    // Try to send email ONLY if we have an access_token (on-behalf-of flow)
    if (accessToken) {
        try {
            console.log('Using provided access_token (on-behalf-of flow)');
            const gmailClient = new GmailClient(accessToken, userId);
            
            if (gmailClient.isAuthenticated()) {
                // Send the email
                const result = await gmailClient.sendEmail({
                    to,
                    subject: emailSubject,
                    body: emailBody,
                    cc,
                    bcc,
                    isHtml: true
                });
                
                const response = {
                    status: 'sent',
                    message: 'Email sent successfully via Gmail API',
                    message_id: result.messageId,
                    theme,
                    to,
                    subject: emailSubject,
                    cc,
                    bcc
                };
                
                console.log(`Email sent successfully: ${result.messageId}`);
                return JSON.stringify(response, null, 2);
            } else {
                console.error('Gmail client not authenticated despite having access_token');
            }
        } catch (error: any) {
            console.error(`Error sending email via Gmail API: ${error.message}`);
            // Fall through to OAuth instructions
        }
    } else {
        console.log('No access_token provided - returning OAuth instructions for agent');
    }
    
    // Fallback: Generate payload for manual sending or agent to use
    // Create the email message in RFC 2822 format
    const messageParts = [
        `To: ${to}`,
        `Subject: ${emailSubject}`,
        'MIME-Version: 1.0',
        'Content-Type: text/html; charset=utf-8',
    ];
    
    if (cc) {
        messageParts.push(`Cc: ${cc}`);
    }
    if (bcc) {
        messageParts.push(`Bcc: ${bcc}`);
    }
    
    messageParts.push(''); // Empty line between headers and body
    messageParts.push(emailBody);
    
    const rawMessage = messageParts.join('\n');
    
    // Encode the message in base64url format as required by Gmail API
    const encodedMessage = Buffer.from(rawMessage, 'utf-8')
        .toString('base64')
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=+$/, '');
    
    // Create the Gmail API payload
    const gmailPayload = {
        raw: encodedMessage
    };
    
    // Build OAuth authorization URL for browser agents (polling-based)
    const baseUrl = process.env.MCP_SERVER_BASE_URL || 'http://localhost:8000';
    
    // Generate session ID for browser agent polling
    const sessionId = uuidv4();
    
    const oauthParams = new URLSearchParams({
        response_type: 'code',
        scope: GMAIL_SCOPES.join(' '),
        state: `browser_agent_${sessionId}`
    });
    const oauthUrl = `${baseUrl}/authorize?${oauthParams.toString()}`;
    const previewUrl = `${baseUrl}/preview/email/${theme.toLowerCase()}?to=${to}`;
    
    // Prepare response with automation instructions for Toqan
    const response = {
        status: 'authorization_required',
        message: 'OAuth authorization needed to send email. Please authorize Gmail access.',
        theme,
        to,
        subject: emailSubject,
        preview_url: previewUrl,
        preview_instructions: `Open this URL in your browser to see the rendered HTML: ${previewUrl}`,
        
        // Browser agent automation instructions - polling-based flow
        agent_action: 'browser_agent_oauth_polling',
        oauth_url: oauthUrl,
        session_id: sessionId,
        expected_result: 'authorization_code',
        automation_available: true,
        action: 'browser_agent_polling',
        
        // CRITICAL INSTRUCTIONS FOR AGENT
        AGENT_MUST_DO: {
            DISPLAY_AS_BUTTON: `Display the OAuth URL as a nice button, not just a link: ${oauthUrl}`,
            CRITICAL_FLOW: 'Show OAuth link + immediately start polling = seamless experience',
            DO_NOT_HIDE_LINK: 'DO NOT hide the OAuth link in reasoning - show it prominently in your response',
            START_POLLING_IMMEDIATELY: 'Start polling right after showing the OAuth link - no waiting',
            NO_CONFIRMATION_NEEDED: "Don't wait for user confirmation - just start polling automatically",
            SEAMLESS_EXPERIENCE: 'User sees link, clicks it, and completion is detected automatically',
            POLL_WITH_BACKOFF: 'Poll for 60 seconds with exponential backoff (1s, 2s, 4s, 8s, then 8s intervals)',
            RANDOMIZE_POLLS: 'Add different parameters to each poll call (attempt number, timestamp) to avoid identical calls error',
            USER_MESSAGE: "Say: 'Click the link - I'm already watching for completion!'"
        },
        
        gmail_api_payload: gmailPayload,
        available_themes: Object.keys(EMAIL_TEMPLATES),
        email_preview: {
            subject: emailSubject,
            body_preview: 'HTML email with themed styling (view in email client for full effect)'
        }
    };
    
    return JSON.stringify(response, null, 2);
}

async function getOAuthUrl(userId: string = 'default'): Promise<string> {
    console.log(`Generating OAuth URL for user: ${userId}`);
    
    try {
        if (!oauthConfig.isConfigured()) {
            return JSON.stringify({
                status: 'error',
                message: 'OAuth not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables.'
            }, null, 2);
        }
        
        // Use our /authorize endpoint, NOT direct Google URL
        const baseUrl = process.env.MCP_SERVER_BASE_URL || 'http://localhost:8000';
        
        // Generate session ID for browser agents 
        const sessionId = uuidv4();
        
        const params = new URLSearchParams({
            response_type: 'code',
            state: `browser_agent_${sessionId}`
        });
        
        // Return our /authorize endpoint which will handle the redirect to Google
        const authUrl = `${baseUrl}/authorize?${params.toString()}`;
        
        console.log(`Generated OAuth URL using MCP /authorize endpoint: ${authUrl}`);
        
        const response = {
            status: 'success',
            auth_url: authUrl,
            session_id: sessionId,
            discovery_endpoint: `${baseUrl}/.well-known/oauth-authorization-server`,
            polling_endpoint: `${baseUrl}/oauth/poll/${sessionId}`,
            status_endpoint: `${baseUrl}/oauth/status/${sessionId}`,
            instructions: [
                '1. User should visit the auth_url in their browser', 
                '2. They will be redirected to Google for authorization',
                '3. After granting permissions, code will be stored for polling',
                '4. Poll the polling_endpoint until you get the authorization code',
                '5. Call exchange_oauth_code tool with the retrieved code'
            ],
            browser_agent_flow: {
                supported: true,
                method: 'polling',
                poll_interval_seconds: 2,
                max_poll_duration_minutes: 10,
                instructions: 'Poll status_endpoint every 2 seconds until status is \'ready\', then call polling_endpoint to get code'
            },
            user_id: userId,
            note: 'This URL uses browser agent polling flow - code will be stored server-side for retrieval'
        };
        
        return JSON.stringify(response, null, 2);
        
    } catch (error: any) {
        console.error(`Error generating OAuth URL: ${error.message}`);
        return JSON.stringify({
            status: 'error',
            message: error.message
        }, null, 2);
    }
}

async function exchangeOAuthCode(code: string, userId: string = 'default'): Promise<string> {
    console.log(`Exchanging OAuth code for user: ${userId}`);
    
    try {
        const gmailClient = new GmailClient(undefined, userId);
        const tokenData = await gmailClient.exchangeCodeForToken(code);
        
        const accessToken = tokenData.access_token;
        const refreshToken = tokenData.refresh_token;
        
        if (!accessToken) {
            throw new Error('No access_token in token response');
        }
        
        const response = {
            status: 'success',
            message: 'Token obtained successfully',
            user_id: userId,
            access_token: accessToken,
            refresh_token: refreshToken,
            expires_in: tokenData.expires_in,
            token_type: tokenData.token_type || 'Bearer',
            scope: tokenData.scope,
            next_steps: [
                'IMPORTANT: Use the access_token in your next send_email call',
                "Example: send_email(to='user@example.com', theme='birthday', access_token='<access_token>')",
                'The access_token is required for the on-behalf-of flow'
            ],
            note: 'Store this access_token - you\'ll need it for send_email calls'
        };
        
        console.log('Token exchange successful. Access token provided to agent.');
        return JSON.stringify(response, null, 2);
        
    } catch (error: any) {
        console.error(`Error exchanging OAuth code: ${error.message}`);
        return JSON.stringify({
            status: 'error',
            message: error.message
        }, null, 2);
    }
}

async function getBrowserAgentOAuthUrl(userId: string = 'default'): Promise<string> {
    console.log(`Generating browser agent OAuth URL for user: ${userId}`);
    
    try {
        if (!oauthConfig.isConfigured()) {
            return JSON.stringify({
                status: 'error',
                message: 'OAuth not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables.'
            }, null, 2);
        }
        
        // Generate unique session ID for this OAuth flow
        const sessionId = uuidv4();
        const baseUrl = process.env.MCP_SERVER_BASE_URL || 'http://localhost:8000';
        
        // Create authorization URL with session tracking
        const params = new URLSearchParams({
            response_type: 'code',
            state: `browser_agent_${sessionId}`
        });
        const authUrl = `${baseUrl}/authorize?${params.toString()}`;
        
        console.log(`Generated browser agent OAuth session: ${sessionId}`);
        
        const response = {
            status: 'success', 
            auth_url: authUrl,
            session_id: sessionId,
            polling_endpoint: `${baseUrl}/oauth/poll/${sessionId}`,
            status_endpoint: `${baseUrl}/oauth/status/${sessionId}`,
            
            // Instructions for browser-based LLM agents
            agent_instructions: {
                step_1: 'Present auth_url to user as clickable link',
                step_2: 'User clicks link and completes OAuth in same browser tab', 
                step_3: 'Poll status_endpoint every 2 seconds (max 10 minutes)',
                step_4: 'When status is \'ready\', call polling_endpoint to get code',
                step_5: 'Call exchange_oauth_code with retrieved code'
            },
            
            polling_config: {
                poll_interval_seconds: 2,
                max_duration_minutes: 10,
                status_check_url: `${baseUrl}/oauth/status/${sessionId}`,
                code_retrieval_url: `${baseUrl}/oauth/poll/${sessionId}`
            },
            
            user_message: `Please click this link to authorize Gmail access: ${authUrl}`,
            technical_note: 'This OAuth flow stores the authorization code server-side for polling by browser agents',
            user_id: userId
        };
        
        return JSON.stringify(response, null, 2);
        
    } catch (error: any) {
        console.error(`Error generating browser agent OAuth URL: ${error.message}`);
        return JSON.stringify({
            status: 'error',
            message: error.message
        }, null, 2);
    }
}

async function pollOAuthCode(
    sessionId: string, 
    attempt?: number, 
    timestamp?: string, 
    randomId?: string
): Promise<string> {
    console.log(`Polling OAuth code for session: ${sessionId} (attempt: ${attempt}, timestamp: ${timestamp}, random: ${randomId})`);
    
    try {
        if (!sessionId) {
            return JSON.stringify({
                status: 'error',
                message: 'Session ID is required'
            }, null, 2);
        }
        
        // Check if session exists and has code
        if (!oauthSessions.has(sessionId)) {
            return JSON.stringify({
                status: 'pending',
                message: 'Waiting for user to complete OAuth authorization...',
                session_id: sessionId,
                action: 'continue_polling'
            }, null, 2);
        }
        
        const sessionData = oauthSessions.get(sessionId)!;
        
        // Check if session expired (10 minutes)
        const now = new Date();
        const tenMinutesAgo = new Date(now.getTime() - 10 * 60 * 1000);
        if (sessionData.timestamp < tenMinutesAgo) {
            oauthSessions.delete(sessionId);
            return JSON.stringify({
                status: 'expired',
                message: 'OAuth session expired. Please restart the flow.',
                action: 'restart_oauth'
            }, null, 2);
        }
        
        // Return the code and clean up session
        const code = sessionData.code;
        oauthSessions.delete(sessionId);
        
        return JSON.stringify({
            status: 'success',
            code,
            message: 'Authorization code retrieved successfully',
            next_step: 'Call exchange_oauth_code with this code'
        }, null, 2);
        
    } catch (error: any) {
        console.error(`Error polling OAuth code: ${error.message}`);
        return JSON.stringify({
            status: 'error',
            message: error.message
        }, null, 2);
    }
}

async function checkOAuthStatus(userId: string = 'default'): Promise<string> {
    console.log(`Checking OAuth status for user: ${userId}`);
    
    try {
        return JSON.stringify({
            status: 'success',
            oauth_configured: oauthConfig.isConfigured(),
            user_id: userId,
            message: oauthConfig.isConfigured() 
                ? 'OAuth is configured and ready'
                : 'OAuth not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables.'
        }, null, 2);
        
    } catch (error: any) {
        console.error(`Error checking OAuth status: ${error.message}`);
        return JSON.stringify({
            status: 'error',
            message: error.message
        }, null, 2);
    }
}

function echoMessage(message: string): string {
    return JSON.stringify({
        status: 'success',
        message: `Echo: ${message}`,
        timestamp: new Date().toISOString()
    }, null, 2);
}

function healthCheck(): string {
    return JSON.stringify({
        status: 'healthy',
        oauth_configured: oauthConfig.isConfigured(),
        base_url: process.env.MCP_SERVER_BASE_URL || 'not set',
        timestamp: new Date().toISOString()
    }, null, 2);
}

function testConnection(): string {
    return JSON.stringify({
        status: 'success',
        message: 'MCP TypeScript server is running and accessible',
        server_name: 'lever-mcp-ts',
        version: '1.0.0',
        timestamp: new Date().toISOString()
    }, null, 2);
}

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
        tools: [
            {
                name: 'list_candidates',
                description: 'List candidates from Lever',
                inputSchema: {
                    type: 'object',
                    properties: {
                        limit: {
                            type: 'number',
                            description: 'Maximum number of candidates to return',
                            default: 10
                        },
                        offset: {
                            type: 'string',
                            description: 'Pagination offset token'
                        }
                    }
                }
            },
            {
                name: 'get_candidate',
                description: 'Get a specific candidate by ID from Lever',
                inputSchema: {
                    type: 'object',
                    properties: {
                        candidateId: {
                            type: 'string',
                            description: 'The ID of the candidate to retrieve'
                        }
                    },
                    required: ['candidateId']
                }
            },
            {
                name: 'create_requisition',
                description: 'Create a new job requisition in Lever',
                inputSchema: {
                    type: 'object',
                    properties: {
                        name: { type: 'string', description: 'The job title/name for the requisition (required)' },
                        business: { type: 'string', description: 'Business unit (required)' },
                        current_status: { type: 'string', description: 'Current status (required)' },
                        global_grade: { type: 'string', description: 'Global grade for the position (required)' },
                        headcountTotal: { type: 'number', description: 'Total headcount for this requisition (required)' },
                        hrbp: { type: 'string', description: 'HRBP name (required)' },
                        job_progress: { type: 'string', description: 'Job progress status (required)' },
                        lastweek_status: { type: 'string', description: 'Last week status (required)' },
                        location: { type: 'string', description: 'The location for the job (required)' },
                        recruiter: { type: 'string', description: 'Recruiter name (required)' },
                        requisitionCode: { type: 'string', description: 'Unique code for the requisition (required)' },
                        team: { type: 'string', description: 'The team the job belongs to (required)' }
                    },
                    required: ['name', 'business', 'current_status', 'global_grade', 'headcountTotal', 'hrbp', 'job_progress', 'lastweek_status', 'location', 'recruiter', 'requisitionCode', 'team']
                }
            },
            {
                name: 'send_email',
                description: 'Generate and send a themed email via Gmail API with OAuth 2.0',
                inputSchema: {
                    type: 'object',
                    properties: {
                        to: { type: 'string', format: 'email', description: 'Recipient email address' },
                        theme: { type: 'string', description: 'The theme for the email (e.g., \'birthday\', \'pirate\', \'space\', \'medieval\', \'superhero\', \'tropical\')' },
                        subject: { type: 'string', description: 'Email subject (optional - will be generated based on theme if not provided)' },
                        cc: { type: 'string', description: 'CC email addresses (comma-separated)' },
                        bcc: { type: 'string', description: 'BCC email addresses (comma-separated)' },
                        access_token: { type: 'string', description: 'OAuth access token from agent (on-behalf-of flow)' },
                        user_id: { type: 'string', default: 'default', description: 'User identifier for token storage' }
                    },
                    required: ['to', 'theme']
                }
            },
            {
                name: 'get_oauth_url',
                description: 'Get OAuth authorization URL for Gmail access',
                inputSchema: {
                    type: 'object',
                    properties: {
                        user_id: { type: 'string', default: 'default', description: 'User identifier for token storage' }
                    }
                }
            },
            {
                name: 'exchange_oauth_code',
                description: 'Exchange OAuth authorization code for access token',
                inputSchema: {
                    type: 'object',
                    properties: {
                        code: { type: 'string', description: 'Authorization code from OAuth callback' },
                        user_id: { type: 'string', default: 'default', description: 'User identifier for token storage' }
                    },
                    required: ['code']
                }
            },
            {
                name: 'get_browser_agent_oauth_url',
                description: 'Get OAuth authorization URL optimized for browser-based LLM agents',
                inputSchema: {
                    type: 'object',
                    properties: {
                        user_id: { type: 'string', default: 'default', description: 'User identifier for token storage' }
                    }
                }
            },
            {
                name: 'poll_oauth_code',
                description: 'Poll for OAuth authorization code by session ID (browser agents)',
                inputSchema: {
                    type: 'object',
                    properties: {
                        session_id: { type: 'string', description: 'OAuth session ID from get_browser_agent_oauth_url' },
                        attempt: { type: 'number', description: 'Optional attempt number to avoid identical tool calls (recommended)' },
                        timestamp: { type: 'string', description: 'Optional timestamp to avoid identical tool calls' },
                        random_id: { type: 'string', description: 'Optional random string to avoid identical tool calls' }
                    },
                    required: ['session_id']
                }
            },
            {
                name: 'check_oauth_status',
                description: 'Check OAuth authentication status',
                inputSchema: {
                    type: 'object',
                    properties: {
                        user_id: { type: 'string', default: 'default', description: 'User identifier' }
                    }
                }
            },
            {
                name: 'echo',
                description: 'Echo a message back',
                inputSchema: {
                    type: 'object',
                    properties: {
                        message: { type: 'string' }
                    },
                    required: ['message']
                }
            },
            {
                name: 'health',
                description: 'Health check',
                inputSchema: { type: 'object' }
            },
            {
                name: 'test_connection',
                description: 'Verify MCP server connectivity and tool execution',
                inputSchema: { type: 'object' }
            }
        ]
    };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;
    
    if (!args) {
        return {
            content: [{
                type: 'text',
                text: 'Error: No arguments provided'
            }],
            isError: true
        };
    }
    
    try {
        let result: string;
        
        switch (name) {
            case 'list_candidates':
                result = await listCandidates(
                    args.limit as number | undefined, 
                    args.offset as string | undefined
                );
                break;
            case 'get_candidate':
                result = await getCandidate(args.candidateId as string);
                break;
            case 'create_requisition':
                result = await createRequisition(
                    args.name as string,
                    args.business as string,
                    args.current_status as string,
                    args.global_grade as string,
                    args.headcountTotal as number,
                    args.hrbp as string,
                    args.job_progress as string,
                    args.lastweek_status as string,
                    args.location as string,
                    args.recruiter as string,
                    args.requisitionCode as string,
                    args.team as string
                );
                break;
            case 'send_email':
                result = await sendEmail(
                    args.to as string,
                    args.theme as string,
                    args.subject as string | undefined,
                    args.cc as string | undefined,
                    args.bcc as string | undefined,
                    args.access_token as string | undefined,
                    (args.user_id as string) || 'default'
                );
                break;
            case 'get_oauth_url':
                result = await getOAuthUrl((args.user_id as string) || 'default');
                break;
            case 'exchange_oauth_code':
                result = await exchangeOAuthCode(
                    args.code as string, 
                    (args.user_id as string) || 'default'
                );
                break;
            case 'get_browser_agent_oauth_url':
                result = await getBrowserAgentOAuthUrl((args.user_id as string) || 'default');
                break;
            case 'poll_oauth_code':
                result = await pollOAuthCode(
                    args.session_id as string,
                    args.attempt as number | undefined,
                    args.timestamp as string | undefined,
                    args.random_id as string | undefined
                );
                break;
            case 'check_oauth_status':
                result = await checkOAuthStatus((args.user_id as string) || 'default');
                break;
            case 'echo':
                result = echoMessage(args.message as string);
                break;
            case 'health':
                result = healthCheck();
                break;
            case 'test_connection':
                result = testConnection();
                break;
            default:
                throw new Error(`Unknown tool: ${name}`);
        }
        
        return {
            content: [
                {
                    type: 'text',
                    text: result
                }
            ]
        };
    } catch (error: any) {
        return {
            content: [
                {
                    type: 'text',
                    text: `Error: ${error.message}`
                }
            ],
            isError: true
        };
    }
});

// Start the server
async function main() {
    const transport = new StdioServerTransport();
    await server.connect(transport);
    console.error('Lever MCP TypeScript server running on stdio');
}

main().catch((error) => {
    console.error('Fatal error in main():', error);
    process.exit(1);
});
