import { test, expect } from '@playwright/test';
import { transformResult } from '../src/services/api';

test.describe('API Transformation Unit Tests', () => {
    test('should transform empty backend result correctly', () => {
        const backendResult: any = {
            metadata: {
                total_documents_scanned: 0,
                documents_by_category: {},
                processing_errors: [],
                processing_warnings: [],
                processing_time_seconds: 0,
            }
        };

        const transformed = transformResult(backendResult);

        expect(transformed.passport).toBeNull();
        expect(transformed.financial).toBeNull();
        expect(transformed.education).toBeNull();
        expect(transformed.cross_validation).toBeNull();
        expect(transformed.metadata.total_documents_scanned).toBe(0);
    });

    test('should transform full backend result correctly', () => {
        const backendResult: any = {
            passport_details: {
                first_name: 'John',
                last_name: 'Doe',
                date_of_birth: '1990-01-01',
                passport_number: 'A1234567',
                issuing_country: 'USA',
                mrz_data: {
                    raw_line1: 'P<USA...',
                    raw_line2: '12345...'
                }
            },
            financial_summary: {
                document_type: 'Bank Statement',
                amount_eur: 15500,
                worthiness_status: 'valid'
            },
            education_summary: {
                student_name: 'John Doe',
                validation_status: 'valid',
                french_equivalent_grade_0_20: 14.5
            },
            cross_validation: {
                name_match: true,
                name_match_score: 1.0
            },
            metadata: {
                total_documents_scanned: 3,
                documents_by_category: { 'passport': 1, 'financial': 1, 'education': 1 },
                processing_errors: [],
                processing_warnings: [],
                processing_time_seconds: 10,
            }
        };

        const transformed = transformResult(backendResult);

        expect(transformed.passport?.first_name).toBe('John');
        expect(transformed.passport?.mrz_line1).toBe('P<USA...');
        expect(transformed.financial?.amount_eur).toBe(15500);
        expect(transformed.education?.french_equivalent_grade_0_20).toBe(14.5);
        expect(transformed.cross_validation?.name_match).toBe(true);
    });

    test('should handle missing metadata by providing defaults', () => {
        const backendResult: any = {
            passport_details: { first_name: 'John' }
        };

        const transformed = transformResult(backendResult);

        expect(transformed.metadata).toBeDefined();
        expect(transformed.metadata.total_documents_scanned).toBe(0);
        expect(transformed.metadata.processing_errors).toEqual([]);
    });
});
