/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type OutcomeInput = {
    category: string;
    outcome: OutcomeInput.outcome;
};
export namespace OutcomeInput {
    export enum outcome {
        WON = 'won',
        REPLIED = 'replied',
        IGNORED = 'ignored',
        HIRED = 'hired',
        LOST = 'lost',
    }
}

