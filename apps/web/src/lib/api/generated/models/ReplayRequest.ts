/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type ReplayRequest = {
    checkpoint_id: string;
    stage?: ReplayRequest.stage;
};
export namespace ReplayRequest {
    export enum stage {
        ANALYSIS = 'analysis',
        PRICING = 'pricing',
        WRITER = 'writer',
        VERIFIER = 'verifier',
        CRITIC = 'critic',
        COMPLIANCE_GUARD = 'compliance_guard',
    }
}

