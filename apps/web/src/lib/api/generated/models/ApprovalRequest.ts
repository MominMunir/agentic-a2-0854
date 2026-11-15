/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type ApprovalRequest = {
    decision: ApprovalRequest.decision;
    text?: (string | null);
    reason?: string;
    approval_token?: string;
};
export namespace ApprovalRequest {
    export enum decision {
        APPROVE = 'approve',
        REJECT = 'reject',
        EDIT = 'edit',
    }
}

