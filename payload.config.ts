import { buildConfig } from 'payload/config';
import { webpackBundler } from '@payloadcms/bundler-webpack';
import { slateEditor } from '@payloadcms/richtext-slate';
import { postgresAdapter } from '@payloadcms/db-postgres';
import { CollectionConfig } from 'payload/types';
import path from 'path';


// Import custom fields and hooks
import { 
  createTenantField, 
  createTimestampFields, 
  industryRoleField,
  searchableTextField 
} from './payload/fields/industry-fields';
import { 
  setTenantContext, 
  filterByTenant 
} from './payload/hooks/tenant-context';
import { 
  invalidateCacheAfterChange, 
  invalidateCacheAfterDelete 
} from './payload/hooks/cache-invalidation';
import { 
  applyIndustryValidation 
} from './payload/hooks/industry-customization';
import { 
  trackOperationStart, 
  trackOperationEnd 
} from './payload/hooks/performance-tracking';

// Multi-tenant collections
const Users: CollectionConfig = {
  slug: 'users',
  auth: {
    tokenExpiration: 7200, // 2 hours
    verify: false,
    maxLoginAttempts: 5,
    lockTime: 600 * 1000, // 10 minutes
    useAPIKey: true, // Enable API key authentication
  },
  admin: {
    useAsTitle: 'email',
    group: 'User Management',
    defaultColumns: ['firstName', 'lastName', 'email', 'role', 'isActive', 'lastLogin'],
    pagination: {
      defaultLimit: 25,
      limits: [10, 25, 50, 100],
    },
  },
  fields: [
    createTenantField(),
    searchableTextField('firstName', 'First Name'),
    searchableTextField('lastName', 'Last Name'),
    {
      name: 'email',
      type: 'email',
      required: true,
      unique: true,
      index: true,
    },
    industryRoleField,
    {
      name: 'isActive',
      type: 'checkbox',
      defaultValue: true,
      index: true,
      admin: {
        position: 'sidebar',
      },
    },
    {
      name: 'companyId',
      type: 'text',
      index: true,
      admin: {
        condition: (data, siblingData) => {
          return ['company_admin', 'company_user'].includes(siblingData.role);
        },
      },
    },
    {
      name: 'profile',
      type: 'json',
      admin: {
        description: 'Additional user profile information',
      },
    },
    {
      name: 'lastLogin',
      type: 'date',
      admin: {
        position: 'sidebar',
        readOnly: true,
      },
    },
    ...createTimestampFields(),
  ],
  hooks: {
    beforeChange: [
      trackOperationStart,
      setTenantContext,
      applyIndustryValidation,
    ],
    afterChange: [
      trackOperationEnd,
      invalidateCacheAfterChange,
    ],
    beforeRead: [filterByTenant],
    afterDelete: [invalidateCacheAfterDelete],
  },
  access: {
    // Row-level security through Payload access control
    read: ({ req: { user } }) => {
      if (user?.role === 'platform_admin') return true;
      return {
        tenantId: {
          equals: user?.tenantId,
        },
      };
    },
    create: ({ req: { user } }) => {
      return user?.role === 'platform_admin' || user?.role === 'account_owner';
    },
    update: ({ req: { user } }) => {
      if (user?.role === 'platform_admin') return true;
      return {
        tenantId: {
          equals: user?.tenantId,
        },
      };
    },
    delete: ({ req: { user } }) => {
      return user?.role === 'platform_admin' || user?.role === 'account_owner';
    },
  },
};

const Tenants: CollectionConfig = {
  slug: 'tenants',
  admin: {
    useAsTitle: 'name',
    group: 'Platform Management',
  },
  fields: [
    {
      name: 'name',
      type: 'text',
      required: true,
    },
    {
      name: 'subdomain',
      type: 'text',
      required: true,
      unique: true,
      index: true,
    },
    {
      name: 'customDomain',
      type: 'text',
      index: true,
    },
    {
      name: 'industryModule',
      type: 'select',
      required: true,
      defaultValue: 'coworking',
      options: [
        { label: 'Coworking', value: 'coworking' },
        { label: 'Government', value: 'government' },
        { label: 'Commercial Real Estate', value: 'commercial_re' },
        { label: 'Hotel', value: 'hotel' },
        { label: 'University', value: 'university' },
        { label: 'Creative Studio', value: 'creative' },
        { label: 'Residential', value: 'residential' },
      ],
      index: true,
    },
    {
      name: 'plan',
      type: 'select',
      required: true,
      defaultValue: 'starter',
      options: [
        { label: 'Starter', value: 'starter' },
        { label: 'Professional', value: 'professional' },
        { label: 'Enterprise', value: 'enterprise' },
      ],
    },
    {
      name: 'isActive',
      type: 'checkbox',
      defaultValue: true,
      index: true,
    },
    {
      name: 'branding',
      type: 'json',
    },
    {
      name: 'settings',
      type: 'json',
    },
    {
      name: 'featureToggles',
      type: 'json',
    },
  ],
  access: {
    read: ({ req: { user } }) => {
      if (user?.role === 'platform_admin') return true;
      return {
        id: {
          equals: user?.tenantId,
        },
      };
    },
    create: ({ req: { user } }) => user?.role === 'platform_admin',
    update: ({ req: { user } }) => {
      if (user?.role === 'platform_admin') return true;
      return {
        id: {
          equals: user?.tenantId,
        },
      };
    },
    delete: ({ req: { user } }) => user?.role === 'platform_admin',
  },
};

const Pages: CollectionConfig = {
  slug: 'pages',
  admin: {
    useAsTitle: 'title',
    group: 'Content Management',
    defaultColumns: ['title', 'slug', 'status', 'updatedAt'],
  },
  versions: {
    maxPerDoc: 10,
    drafts: true,
  },
  fields: [
    {
      name: 'tenantId',
      type: 'text',
      required: true,
      index: true,
      admin: {
        position: 'sidebar',
      },
    },
    {
      name: 'title',
      type: 'text',
      required: true,
    },
    {
      name: 'slug',
      type: 'text',
      required: true,
      index: true,
      admin: {
        position: 'sidebar',
      },
    },
    {
      name: 'content',
      type: 'richText',
      editor: slateEditor({
        admin: {
          elements: [
            'h1',
            'h2',
            'h3',
            'h4',
            'blockquote',
            'ul',
            'ol',
            'link',
            'textAlign',
          ],
          leaves: ['bold', 'italic', 'underline', 'strikethrough', 'code'],
        },
      }),
    },
    {
      name: 'contentBlocks',
      type: 'json',
      admin: {
        description: 'Dynamic content blocks for page builder',
      },
    },
    {
      name: 'metaTitle',
      type: 'text',
      admin: {
        position: 'sidebar',
      },
    },
    {
      name: 'metaDescription',
      type: 'textarea',
      admin: {
        position: 'sidebar',
      },
    },
    {
      name: 'status',
      type: 'select',
      required: true,
      defaultValue: 'draft',
      options: [
        { label: 'Draft', value: 'draft' },
        { label: 'Published', value: 'published' },
        { label: 'Archived', value: 'archived' },
      ],
      index: true,
      admin: {
        position: 'sidebar',
      },
    },
    {
      name: 'isHomepage',
      type: 'checkbox',
      defaultValue: false,
      index: true,
      admin: {
        position: 'sidebar',
      },
    },
    {
      name: 'templateId',
      type: 'text',
      admin: {
        position: 'sidebar',
      },
    },
    {
      name: 'searchKeywords',
      type: 'text',
      admin: {
        description: 'Auto-generated from content for search optimization',
        readOnly: true,
      },
    },
  ],
  hooks: {
    beforeChange: [
      ({ req, data }) => {
        // Set tenant context
        if (req.user && req.user.tenantId) {
          data.tenantId = req.user.tenantId;
        }
        
        // Generate search keywords from content
        if (data.content) {
          // Extract text from rich text content
          const textContent = JSON.stringify(data.content).replace(/<[^>]*>/g, ' ');
          data.searchKeywords = textContent.toLowerCase().replace(/[^\w\s]/g, ' ').trim();
        }
        
        return data;
      },
    ],
  },
  access: {
    read: ({ req: { user } }) => {
      if (user?.role === 'platform_admin') return true;
      return {
        tenantId: {
          equals: user?.tenantId,
        },
      };
    },
    create: ({ req: { user } }) => {
      const allowedRoles = ['platform_admin', 'account_owner', 'administrator', 'property_manager'];
      return allowedRoles.includes(user?.role);
    },
    update: ({ req: { user } }) => {
      if (user?.role === 'platform_admin') return true;
      const allowedRoles = ['account_owner', 'administrator', 'property_manager'];
      if (!allowedRoles.includes(user?.role)) return false;
      
      return {
        tenantId: {
          equals: user?.tenantId,
        },
      };
    },
    delete: ({ req: { user } }) => {
      if (user?.role === 'platform_admin') return true;
      const allowedRoles = ['account_owner', 'administrator', 'property_manager'];
      if (!allowedRoles.includes(user?.role)) return false;
      
      return {
        tenantId: {
          equals: user?.tenantId,
        },
      };
    },
  },
};

const Leads: CollectionConfig = {
  slug: 'leads',
  admin: {
    useAsTitle: 'email',
    group: 'Lead Management',
    defaultColumns: ['firstName', 'lastName', 'email', 'status', 'createdAt'],
  },
  fields: [
    {
      name: 'tenantId',
      type: 'text',
      required: true,
      index: true,
      admin: {
        position: 'sidebar',
      },
    },
    {
      name: 'firstName',
      type: 'text',
      required: true,
    },
    {
      name: 'lastName',
      type: 'text',
      required: true,
    },
    {
      name: 'email',
      type: 'email',
      required: true,
      index: true,
    },
    {
      name: 'phone',
      type: 'text',
    },
    {
      name: 'company',
      type: 'text',
    },
    {
      name: 'status',
      type: 'select',
      required: true,
      defaultValue: 'new_inquiry',
      options: [
        { label: 'New Inquiry', value: 'new_inquiry' },
        { label: 'Tour Scheduled', value: 'tour_scheduled' },
        { label: 'Tour Completed', value: 'tour_completed' },
        { label: 'Converted', value: 'converted' },
        { label: 'Closed', value: 'closed' },
      ],
      index: true,
    },
    {
      name: 'source',
      type: 'text',
      index: true,
    },
    {
      name: 'notes',
      type: 'textarea',
    },
    {
      name: 'customFields',
      type: 'json',
    },
    {
      name: 'assignedTo',
      type: 'relationship',
      relationTo: 'users',
      index: true,
    },
    {
      name: 'tourScheduledAt',
      type: 'date',
      admin: {
        date: {
          pickerAppearance: 'dayAndTime',
        },
      },
    },
    {
      name: 'tourCompletedAt',
      type: 'date',
      admin: {
        date: {
          pickerAppearance: 'dayAndTime',
        },
      },
    },
    {
      name: 'convertedAt',
      type: 'date',
      admin: {
        date: {
          pickerAppearance: 'dayAndTime',
        },
      },
    },
  ],
  hooks: {
    beforeChange: [
      ({ req, data }) => {
        // Set tenant context
        if (req.user && req.user.tenantId) {
          data.tenantId = req.user.tenantId;
        }
        
        // Auto-set conversion timestamp
        if (data.status === 'converted' && !data.convertedAt) {
          data.convertedAt = new Date();
        }
        
        return data;
      },
    ],
  },
  access: {
    read: ({ req: { user } }) => {
      if (user?.role === 'platform_admin') return true;
      return {
        tenantId: {
          equals: user?.tenantId,
        },
      };
    },
    create: ({ req: { user } }) => {
      const allowedRoles = ['platform_admin', 'account_owner', 'administrator', 'property_manager', 'front_desk'];
      return allowedRoles.includes(user?.role);
    },
    update: ({ req: { user } }) => {
      if (user?.role === 'platform_admin') return true;
      const allowedRoles = ['account_owner', 'administrator', 'property_manager', 'front_desk'];
      if (!allowedRoles.includes(user?.role)) return false;
      
      return {
        tenantId: {
          equals: user?.tenantId,
        },
      };
    },
    delete: ({ req: { user } }) => {
      if (user?.role === 'platform_admin') return true;
      const allowedRoles = ['account_owner', 'administrator', 'property_manager'];
      if (!allowedRoles.includes(user?.role)) return false;
      
      return {
        tenantId: {
          equals: user?.tenantId,
        },
      };
    },
  },
};

export default buildConfig({
  admin: {
    user: Users.slug,
    bundler: webpackBundler(),
  },
  editor: slateEditor({}),
  collections: [Users, Tenants, Pages, Leads],
  plugins: [],
  typescript: {
    outputFile: path.resolve(__dirname, 'payload-types.ts'),
  },
  graphQL: {
    schemaOutputFile: path.resolve(__dirname, 'generated-schema.graphql'),
  },
  db: postgresAdapter({
    pool: {
      connectionString: process.env.DATABASE_URL || 'postgresql://localhost:5432/claude-app',
    },
  }),
  serverURL: process.env.PAYLOAD_PUBLIC_SERVER_URL || 'http://localhost:3000',
  cors: [
    process.env.PAYLOAD_PUBLIC_SERVER_URL || 'http://localhost:3000',
    process.env.FRONTEND_URL || 'http://localhost:3001',
  ],
  csrf: [
    process.env.PAYLOAD_PUBLIC_SERVER_URL || 'http://localhost:3000',
    process.env.FRONTEND_URL || 'http://localhost:3001',
  ],
  // Performance and security settings
  rateLimit: {
    max: 1000,
    window: 15 * 60 * 1000,
    skip: (req) => {
      return req.headers['x-internal-api'] === 'true';
    },
  },
  // Enable caching
  // Localization support
  // File upload optimization
  // Email configuration
  // Hooks for performance monitoring
});
