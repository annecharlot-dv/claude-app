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
  options: async ({ req }) => {
    // Get tenant industry to determine available roles
    let tenant;
    if (req.user?.tenantId) {
      try {
        tenant = await req.payload.findByID({
          collection: 'tenants',
          id: req.user.tenantId,
        });
      } catch (error) {
        console.error('Failed to fetch tenant for role options:', error);
      }
    }

    const industryConfig = tenant ? INDUSTRY_CONFIGS[tenant.industryModule] : null;
    const baseRoles = [
      { label: 'Platform Admin', value: 'platform_admin' },
      { label: 'Account Owner', value: 'account_owner' },
      { label: 'Administrator', value: 'administrator' },
      { label: 'Property Manager', value: 'property_manager' },
      { label: 'Front Desk', value: 'front_desk' },
      { label: 'Maintenance', value: 'maintenance' },
      { label: 'Security', value: 'security' },
    ];

    // Add industry-specific roles
    if (industryConfig?.userRoles) {
      const industryRoles = industryConfig.userRoles.map((role: string) => ({
        label: role.replace('_', ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()),
        value: role,
      }));
      baseRoles.push(...industryRoles);
    }

    return baseRoles;
  },
};

// Dynamic lead source field
export const leadSourceField: Field = {
  name: 'source',
  type: 'select',
  admin: {
    description: 'How this lead was acquired',
  },
  options: async ({ req }) => {
    let tenant;
    if (req.user?.tenantId) {
      try {
        tenant = await req.payload.findByID({
          collection: 'tenants',
          id: req.user.tenantId,
        });
      } catch (error) {
        console.error('Failed to fetch tenant for source options:', error);
      }
    }

    const industryConfig = tenant ? INDUSTRY_CONFIGS[tenant.industryModule] : null;
    const baseSources = [
      { label: 'Website', value: 'website' },
      { label: 'Referral', value: 'referral' },
      { label: 'Phone', value: 'phone' },
      { label: 'Walk-in', value: 'walk_in' },
    ];

    if (industryConfig?.leadSources) {
      return industryConfig.leadSources.map((source: string) => ({
        label: source.replace('_', ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()),
        value: source,
      }));
    }

    return baseSources;
  },
};

// Industry-specific custom fields
export const industryCustomFields: Field = {
  name: 'customFields',
  type: 'json',
  admin: {
    description: 'Industry-specific additional fields',
    components: {
      Field: 'payload/fields/IndustryCustomFieldsComponent',
    },
  },
  validate: async (value, { req }) => {
    // Get tenant to validate required fields
    let tenant;
    if (req.user?.tenantId) {
      try {
        tenant = await req.payload.findByID({
          collection: 'tenants',
          id: req.user.tenantId,
        });
      } catch (error) {
        return true; // Skip validation if tenant fetch fails
      }
    }

    const industryConfig = tenant ? INDUSTRY_CONFIGS[tenant.industryModule] : null;
    if (!industryConfig?.requiredFields) return true;

    // Check required fields
    const missingFields = industryConfig.requiredFields.filter(
      (field: string) => !value?.[field]
    );

    if (missingFields.length > 0) {
      return `Missing required fields: ${missingFields.join(', ')}`;
    }

    return true;
  },
};

// Tenant-aware relationship field
export const tenantRelationshipField = (collection: string): Field => ({
  name: collection,
  type: 'relationship',
  relationTo: collection,
  filterOptions: ({ req }) => {
    // Filter relationships by tenant
    if (req.user?.tenantId && req.user.role !== 'platform_admin') {
      return {
        tenantId: {
          equals: req.user.tenantId,
        },
      };
    }
    return {};
  },
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
  hooks: {
    afterChange: [
      async ({ value, req, doc }) => {
        // Update search index
        if (value && doc.tenantId) {
          try {
            await fetch('/api/search/index', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'X-Internal-API': 'true',
              },
              body: JSON.stringify({
                collection: req.collection?.config?.slug,
                documentId: doc.id,
                tenantId: doc.tenantId,
                field: name,
                value,
              }),
            });
          } catch (error) {
            console.error('Search indexing failed:', error);
          }
        }
      },
    ],
  },
});

// Rich text field with industry-specific templates
export const industryRichTextField = (name: string): Field => ({
  name,
  type: 'richText',
  admin: {
    elements: [
      'h1', 'h2', 'h3', 'h4',
      'blockquote',
      'ul', 'ol', 'li',
      'link',
      'textAlign',
    ],
    leaves: [
      'bold', 'italic', 'underline', 'strikethrough', 'code',
    ],
  },
  hooks: {
    beforeChange: [
      async ({ value, req }) => {
        // Add industry-specific content processing
        if (req.user?.tenantId) {
          try {
            const tenant = await req.payload.findByID({
              collection: 'tenants',
              id: req.user.tenantId,
            });
            
            // Apply industry-specific content transformations
            if (tenant.industryModule === 'government') {
              // Add accessibility improvements for government content
              // This would process the rich text to ensure compliance
            }
          } catch (error) {
            console.error('Industry content processing failed:', error);
          }
        }
        return value;
      },
    ],
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
  defaultValue: ({ req }) => req.user?.tenantId,
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