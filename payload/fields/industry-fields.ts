import { Field } from 'payload/types';
import { INDUSTRY_CONFIGS } from '../hooks/industry-customization';

/**
 * Industry-Specific Custom Fields
 * Reusable field configurations for different industries
 */

// Dynamic role field based on tenant industry
export const industryRoleField: Field = {
  name: 'role',
  type: 'select',
  required: true,
  admin: {
    description: 'User role within the organization',
  },
  options: [
    { label: 'Platform Admin', value: 'platform_admin' },
    { label: 'Account Owner', value: 'account_owner' },
    { label: 'Administrator', value: 'administrator' },
    { label: 'Property Manager', value: 'property_manager' },
    { label: 'Front Desk', value: 'front_desk' },
    { label: 'Maintenance', value: 'maintenance' },
    { label: 'Security', value: 'security' },
  ],
};

// Dynamic lead source field
export const leadSourceField: Field = {
  name: 'source',
  type: 'select',
  admin: {
    description: 'How this lead was acquired',
  },
  options: [
    { label: 'Website', value: 'website' },
    { label: 'Referral', value: 'referral' },
    { label: 'Phone', value: 'phone' },
    { label: 'Walk-in', value: 'walk_in' },
  ],
};

// Industry-specific custom fields
export const industryCustomFields: Field = {
  name: 'customFields',
  type: 'json',
  admin: {
    description: 'Industry-specific additional fields',
  },
};

// Tenant-aware relationship field
export const tenantRelationshipField = (collection: string): Field => ({
  name: collection,
  type: 'relationship',
  relationTo: collection,
  admin: {
    description: `Related ${collection} within your organization`,
  },
});

// Industry module field for tenants
export const industryModuleField: Field = {
  name: 'industryModule',
  type: 'select',
  required: true,
  defaultValue: 'coworking',
  options: [
    { label: 'Coworking Space', value: 'coworking' },
    { label: 'Government Facility', value: 'government' },
    { label: 'Commercial Real Estate', value: 'commercial_re' },
    { label: 'Hotel/Hospitality', value: 'hotel' },
    { label: 'University', value: 'university' },
    { label: 'Creative Studio', value: 'creative' },
    { label: 'Residential', value: 'residential' },
  ],
  admin: {
    description: 'Industry module determines available features and terminology',
  },
};

// Performance-optimized text field with search indexing
export const searchableTextField = (name: string, label: string): Field => ({
  name,
  type: 'text',
  label,
  index: true,
  admin: {
    description: `${label} (searchable)`,
  },
});

// Rich text field with industry-specific templates
export const industryRichTextField = (name: string): Field => ({
  name,
  type: 'richText',
  admin: {
    description: 'Rich text content',
  },
});

// Export field factory functions
export const createTenantField = (): Field => ({
  name: 'tenantId',
  type: 'text',
  required: true,
  index: true,
  admin: {
    position: 'sidebar',
    readOnly: true,
    description: 'Automatically set based on your organization',
  },
  access: {
    update: ({ req }) => req.user?.role === 'platform_admin',
  },
  defaultValue: 'default-tenant',
});

export const createTimestampFields = (): Field[] => [
  {
    name: 'createdAt',
    type: 'date',
    admin: {
      position: 'sidebar',
      readOnly: true,
    },
    hooks: {
      beforeChange: [
        ({ req, operation, value }) => {
          if (operation === 'create') {
            return new Date();
          }
          return value;
        },
      ],
    },
  },
  {
    name: 'updatedAt',
    type: 'date',
    admin: {
      position: 'sidebar',
      readOnly: true,
    },
    hooks: {
      beforeChange: [
        () => new Date(),
      ],
    },
  },
];
