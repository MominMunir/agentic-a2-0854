/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ApprovalRequest } from '../models/ApprovalRequest';
import type { AuthResponse } from '../models/AuthResponse';
import type { Body_upload_api_portfolio_upload_post } from '../models/Body_upload_api_portfolio_upload_post';
import type { CalendarHold } from '../models/CalendarHold';
import type { Credentials } from '../models/Credentials';
import type { DraftEdit } from '../models/DraftEdit';
import type { EmailDraft } from '../models/EmailDraft';
import type { JobListResponse } from '../models/JobListResponse';
import type { OutcomeInput } from '../models/OutcomeInput';
import type { Profile } from '../models/Profile';
import type { ReplayRequest } from '../models/ReplayRequest';
import type { RunResponse } from '../models/RunResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class DefaultService {
    /**
     * Register
     * @param requestBody
     * @returns AuthResponse Successful Response
     * @throws ApiError
     */
    public static registerApiAuthRegisterPost(
        requestBody: Credentials,
    ): CancelablePromise<AuthResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/auth/register',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Login
     * @param requestBody
     * @returns AuthResponse Successful Response
     * @throws ApiError
     */
    public static loginApiAuthLoginPost(
        requestBody: Credentials,
    ): CancelablePromise<AuthResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/auth/login',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Logout
     * @returns any Successful Response
     * @throws ApiError
     */
    public static logoutApiAuthLogoutPost(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/auth/logout',
        });
    }
    /**
     * Me
     * @returns AuthResponse Successful Response
     * @throws ApiError
     */
    public static meApiAuthMeGet(): CancelablePromise<AuthResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/auth/me',
        });
    }
    /**
     * Health
     * @returns any Successful Response
     * @throws ApiError
     */
    public static healthApiHealthGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/health',
        });
    }
    /**
     * Get Settings
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getSettingsApiSettingsGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/settings',
        });
    }
    /**
     * Update Settings
     * @param requestBody
     * @returns AuthResponse Successful Response
     * @throws ApiError
     */
    public static updateSettingsApiSettingsPatch(
        requestBody: Profile,
    ): CancelablePromise<AuthResponse> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/settings',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Forget
     * @param kind
     * @param key
     * @returns any Successful Response
     * @throws ApiError
     */
    public static forgetApiMemoryKindKeyDelete(
        kind: string,
        key: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/memory/{kind}/{key}',
            path: {
                'kind': kind,
                'key': key,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Jobs
     * @param query
     * @returns JobListResponse Successful Response
     * @throws ApiError
     */
    public static jobsApiJobsGet(
        query: string = '',
    ): CancelablePromise<JobListResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/jobs',
            query: {
                'query': query,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Job Detail
     * @param jobId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static jobDetailApiJobsJobIdGet(
        jobId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/jobs/{job_id}',
            path: {
                'job_id': jobId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Analyze
     * @param jobId
     * @param agency
     * @returns any Successful Response
     * @throws ApiError
     */
    public static analyzeApiJobsJobIdAnalyzePost(
        jobId: string,
        agency: boolean = false,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/jobs/{job_id}/analyze',
            path: {
                'job_id': jobId,
            },
            query: {
                'agency': agency,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Agency Fit
     * @param jobId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static agencyFitApiJobsJobIdAgencyGet(
        jobId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/jobs/{job_id}/agency',
            path: {
                'job_id': jobId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Skip
     * @param jobId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static skipApiJobsJobIdSkipPost(
        jobId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/jobs/{job_id}/skip',
            path: {
                'job_id': jobId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Runs
     * @returns RunResponse Successful Response
     * @throws ApiError
     */
    public static runsApiRunsGet(): CancelablePromise<Array<RunResponse>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/runs',
        });
    }
    /**
     * Get Run
     * @param runId
     * @returns RunResponse Successful Response
     * @throws ApiError
     */
    public static getRunApiRunsRunIdGet(
        runId: string,
    ): CancelablePromise<RunResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/runs/{run_id}',
            path: {
                'run_id': runId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Events
     * @param runId
     * @param after
     * @returns any Successful Response
     * @throws ApiError
     */
    public static eventsApiRunsRunIdEventsGet(
        runId: string,
        after?: number,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/runs/{run_id}/events',
            path: {
                'run_id': runId,
            },
            query: {
                'after': after,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Trace
     * @param runId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static traceApiRunsRunIdTraceGet(
        runId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/runs/{run_id}/trace',
            path: {
                'run_id': runId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * History
     * @param runId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static historyApiRunsRunIdHistoryGet(
        runId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/runs/{run_id}/history',
            path: {
                'run_id': runId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Retry Run
     * @param runId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static retryRunApiRunsRunIdRetryPost(
        runId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/runs/{run_id}/retry',
            path: {
                'run_id': runId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Edit Draft
     * @param runId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static editDraftApiRunsRunIdDraftPatch(
        runId: string,
        requestBody: DraftEdit,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/runs/{run_id}/draft',
            path: {
                'run_id': runId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Approve
     * @param runId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static approveApiRunsRunIdApprovePost(
        runId: string,
        requestBody: ApprovalRequest,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/runs/{run_id}/approve',
            path: {
                'run_id': runId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Pipeline
     * @returns any Successful Response
     * @throws ApiError
     */
    public static pipelineApiPipelineGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/pipeline',
        });
    }
    /**
     * Regenerate
     * @param runId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static regenerateApiRunsRunIdRegeneratePost(
        runId: string,
        requestBody: Record<string, any>,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/runs/{run_id}/regenerate',
            path: {
                'run_id': runId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Outcome
     * @param jobId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static outcomeApiJobsJobIdOutcomePost(
        jobId: string,
        requestBody: OutcomeInput,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/jobs/{job_id}/outcome',
            path: {
                'job_id': jobId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Messages
     * @returns any Successful Response
     * @throws ApiError
     */
    public static messagesApiMessagesGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/messages',
        });
    }
    /**
     * Draft Message
     * @param conversationId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static draftMessageApiMessagesConversationIdDraftPost(
        conversationId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/messages/{conversation_id}/draft',
            path: {
                'conversation_id': conversationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Upload
     * @param formData
     * @returns any Successful Response
     * @throws ApiError
     */
    public static uploadApiPortfolioUploadPost(
        formData: Body_upload_api_portfolio_upload_post,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/portfolio/upload',
            formData: formData,
            mediaType: 'multipart/form-data',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Analytics
     * @returns any Successful Response
     * @throws ApiError
     */
    public static analyticsApiAnalyticsGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/analytics',
        });
    }
    /**
     * Calendar Hold
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static calendarHoldApiWorkspaceHoldPost(
        requestBody: CalendarHold,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/workspace/hold',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Email Draft
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static emailDraftApiWorkspaceEmailDraftPost(
        requestBody: EmailDraft,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/workspace/email-draft',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Portfolio Access Token
     * @returns any Successful Response
     * @throws ApiError
     */
    public static portfolioAccessTokenApiPortfolioAccessTokenPost(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/portfolio/access-token',
        });
    }
    /**
     * Portfolio Items
     * @returns any Successful Response
     * @throws ApiError
     */
    public static portfolioItemsApiPortfolioGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/portfolio',
        });
    }
    /**
     * Delete Evidence
     * @param evidenceId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteEvidenceApiPortfolioEvidenceIdDelete(
        evidenceId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/portfolio/{evidence_id}',
            path: {
                'evidence_id': evidenceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Replay Run
     * @param runId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static replayRunApiRunsRunIdReplayPost(
        runId: string,
        requestBody: ReplayRequest,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/runs/{run_id}/replay',
            path: {
                'run_id': runId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
