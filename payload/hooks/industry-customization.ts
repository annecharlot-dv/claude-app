import { CollectionBeforeChangeHook, FieldHook } from 'payload/types';

/**
 * Industry Customization Hooks
 * Apply industry-specific business rules and terminology
 */

// Industry-specific field configurations
const INDUSTRY_CONFIGS = {
  coworking: {
    userRoles: ['member', 'company_admin', 'company_user'],
    leadSources: ['website', 'referral', 'event', 'social_media'],
    pageTemplates: ['homepage', 'pricing', 'community', 'events'],
    requiredFields: ['company'],
  },
  government: {
    userRoles: ['citizen', 'staff', 'department_head'],
    leadSources: ['website', 'phone', 'walk_in', 'referral'],
    pageTemplates: ['homepage', 'services', 'transparency', 'contact'],
    requiredFields: ['department'],
  },
  hotel: {
    userRoles: ['guest', 'staff', 'manager'],
    leadSources: ['website', 'booking_platform', 'phone', 'walk_in'],
    pageTemplates: ['homepage', 'rooms', 'amenities', 'booking'],
    requiredFields: ['check_in_date', 'check_out_date'],
  },
  university: {
    userRoles: ['student', 'faculty', 'staff', 'admin'],
    leadSources: ['website', 'student_referral', 'faculty_request', 'event'],
    pageTemplates: ['homepage', 'facilities', 'booking_rules', 'calendar'],
    requiredFields: ['department', 'student_id'],
  },
  creative: {
    userRoles: ['artist', 'studio_manager', 'collaborator'],
    leadSources: ['website', 'artist_referral', 'exhibition', 'social_media'],
    pageTemplates: ['homepage', 'studios', 'gallery', 'community'],
    requiredFields: ['art_medium', 'project_type'],
  },
  residential: {
    userRoles: ['resident', 'property_manager', 'maintenance'],
    leadSources: ['website', 'resident_referral', 'property_listing'],
    pageTemplates: ['homepage', 'amenities', 'community', 'maintenance'],
    requiredFields: ['unit_number', 'lease_type'],
  },
};

// Hook to apply industry-specific validation
export const applyIndustryValidation: CollectionBeforeChangeHook = async ({
  data,
  req,
  operation,
  collection,
}) => {
  // Get tenant to determine industry
  let tenant;
  if (data.tenantId) {
    const tenantResult = await req.payload.findByID({
      collection: 'tenants',
      id: data.tenantId,
    });
    tenant = tenantResult;
  } else if (req.user?.tenantId) {
    const tenantResult = await req.payload.findByID({
      collection: 'tenants',
      id: req.user.tenantId,
    });
    tenant = tenantResult;
  }

  if (!tenant) return data;

  const industryConfig = (INDUSTRY_CONFIGS as any)[tenant.industryModule];
  if (!industryConfig) return data;

  // Apply industry-specific validation based on collection
  switch (collection.slug) {
    case 'users':
      return validateUserForIndustry(data, industryConfig);
    case 'leads':
      return validateLeadForIndustry(data, industryConfig);
    case 'pages':
      return validatePageForIndustry(data, industryConfig);
    default:
      return data;
  }
};

// Industry-specific user validation
const validateUserForIndustry = (data: any, config: any) => {
  // Validate role is appropriate for industry
  if (data.role && !config.userRoles.includes(data.role)) {
    // Map generic roles to industry-specific ones
    const roleMapping = {
      member: config.userRoles[0], // First role is typically the basic user
    };
    
    if ((roleMapping as any)[data.role]) {
      data.role = (roleMapping as any)[data.role];
    }
  }

  return data;
};

// Industry-specific lead validation
const validateLeadForIndustry = (data: any, config: any) => {
  // Validate source is appropriate for industry
  if (data.source && !config.leadSources.includes(data.source)) {
    data.source = 'website'; // Default fallback
  }

  // Ensure required fields are present
  config.requiredFields.forEach((field: string) => {
    if (!data.customFields?.[field] && !data[field]) {
      if (!data.customFields) data.customFields = {};
      data.customFields[field] = null; // Mark as required
    }
  });

  return data;
};

// Industry-specific page validation
const validatePageForIndustry = (data: any, config: any) => {
  // Validate template is appropriate for industry
  if (data.templateId) {
    // This would check against available templates for the industry
    // Implementation depends on your template system
  }

  return data;
};

// Field hook for dynamic options based on industry
export const getIndustryOptions: FieldHook = async ({
  req,
  data,
}) => {
  // Get tenant industry
  let tenant;
  if (data?.tenantId) {
    tenant = await req.payload.findByID({
      collection: 'tenants',
      id: data.tenantId,
    });
  } else if (req.user?.tenantId) {
    tenant = await req.payload.findByID({
      collection: 'tenants',
      id: req.user.tenantId,
    });
  }

  if (!tenant) return [];

  const industryConfig = (INDUSTRY_CONFIGS as any)[tenant.industryModule];
  return industryConfig ? Object.keys(industryConfig) : [];
};

// Hook to customize field labels based on industry
export const customizeFieldLabels = (industryModule: string) => {
  const labelMappings = {
    coworking: {
      'users': 'Members',
      'leads': 'Prospects',
      'bookings': 'Space Reservations',
    },
    government: {
      'users': 'Citizens',
      'leads': 'Service Requests',
      'bookings': 'Facility Reservations',
    },
    hotel: {
      'users': 'Guests',
      'leads': 'Inquiries',
      'bookings': 'Room Reservations',
    },
    university: {
      'users': 'Students & Faculty',
      'leads': 'Booking Requests',
      'bookings': 'Room Bookings',
    },
    creative: {
      'users': 'Artists',
      'leads': 'Studio Inquiries',
      'bookings': 'Studio Reservations',
    },
    residential: {
      'users': 'Residents',
      'leads': 'Rental Inquiries',
      'bookings': 'Amenity Reservations',
    },
  };

  return (labelMappings as any)[industryModule] || {};
};

// Export industry configurations for use in field definitions
export { INDUSTRY_CONFIGS };
