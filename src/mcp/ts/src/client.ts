import axios, { AxiosInstance } from 'axios';

export interface LeverCandidate {
    id: string;
    name: string;
    email: string;
    // Add other fields as needed
    [key: string]: any;
}

export interface LeverCandidateListResponse {
    data: LeverCandidate[];
    hasNext: boolean;
    next?: string;
}

export interface RequisitionData {
    name: string;
    location: string;
    team: string;
    [key: string]: any;
}

export class LeverClient {
    private apiKey: string;
    private baseUrl: string;
    private client: AxiosInstance;

    constructor(apiKey?: string) {
        this.apiKey = apiKey || process.env.LEVER_API_KEY || '';
        if (!this.apiKey) {
            throw new Error('LEVER_API_KEY environment variable is not set');
        }

        this.baseUrl = process.env.LEVER_API_BASE_URL || 'https://api.lever.co/v1';
        
        // Lever uses Basic Auth with the API key as the username and an empty password
        const authString = `${this.apiKey}:`;
        const encodedAuth = Buffer.from(authString).toString('base64');
        
        this.client = axios.create({
            baseURL: this.baseUrl,
            headers: {
                'Authorization': `Basic ${encodedAuth}`,
                'Content-Type': 'application/json'
            }
        });
    }

    async getCandidates(limit: number = 10, offset?: string): Promise<LeverCandidateListResponse> {
        const params: any = { limit };
        if (offset) {
            params.offset = offset;
        }

        const response = await this.client.get('/candidates', { params });
        return response.data;
    }

    async getCandidate(candidateId: string): Promise<LeverCandidate> {
        const response = await this.client.get(`/candidates/${candidateId}`);
        return response.data;
    }

    async createRequisition(data: RequisitionData): Promise<any> {
        const response = await this.client.post('/requisitions', data);
        return response.data;
    }
}
