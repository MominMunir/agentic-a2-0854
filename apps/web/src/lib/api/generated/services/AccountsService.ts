/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { GithubInput } from '../models/GithubInput';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class AccountsService {
    /**
     * Connect
     * @returns any Successful Response
     * @throws ApiError
     */
    public static connectApiAccountsUpworkConnectGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/accounts/upwork/connect',
        });
    }
    /**
     * Callback
     * @param code
     * @param state
     * @returns any Successful Response
     * @throws ApiError
     */
    public static callbackApiAccountsUpworkCallbackGet(
        code: string,
        state: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/accounts/upwork/callback',
            query: {
                'code': code,
                'state': state,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Official Tools
     * @returns any Successful Response
     * @throws ApiError
     */
    public static officialToolsApiAccountsUpworkToolsGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/accounts/upwork/tools',
        });
    }
    /**
     * Tool Map
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static toolMapApiAccountsUpworkToolMapPost(
        requestBody: Record<string, string>,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/accounts/upwork/tool-map',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Github Ingest
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static githubIngestApiAccountsGithubIngestPost(
        requestBody: GithubInput,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/accounts/github/ingest',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
