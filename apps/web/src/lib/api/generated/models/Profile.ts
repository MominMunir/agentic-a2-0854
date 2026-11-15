/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type Profile = {
    persona?: Profile.persona;
    hourly_rate?: number;
    minimum_project_budget?: number;
    weekly_connects_budget?: number;
    saved_search?: string;
    autonomy?: Profile.autonomy;
};
export namespace Profile {
    export enum persona {
        ML = 'ml',
        WEB = 'web',
        DATA = 'data',
        OWN = 'own',
    }
    export enum autonomy {
        REVIEW = 'review',
        AUTO_SKIP = 'auto_skip',
    }
}

