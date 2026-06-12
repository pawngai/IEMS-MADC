import React from 'react';
import '@testing-library/jest-dom';

import { buildSwitchTargets } from '@/app/layout/Layout';
import { canEnterEssPortal } from '@/modules/identity_access/model/portalAccessRules';

describe('Layout dual-role portal switching', () => {
  test('requires employee authority and employee id for ESS portal eligibility', () => {
    expect(
      canEnterEssPortal({
        user: { authorities: ['SYSTEM_ADMIN'], employee_id: '' },
        canAny: () => true,
        canAccessEssPortal: () => true,
      })
    ).toBe(false);

    expect(
      canEnterEssPortal({
        user: { authorities: ['EMPLOYEE'], employee_id: 'EMP-1' },
        canAny: () => true,
        canAccessEssPortal: () => true,
      })
    ).toBe(true);
  });

  test('includes both departmental and global switch targets for dual-role users', () => {
    const targets = buildSwitchTargets({
      isSystemAdmin: false,
      canDepartmentScopedPortal: true,
      hasDepartmentalAuthority: true,
      hasNonEmployeeAuthority: true,
      canAdminPortal: false,
      isGlobalRole: true,
      canEssPortal: false,
      essHomePath: '/ess/dashboard',
      authorities: ['GLOBAL_DATA_ENTRY', 'DEPT_DATA_ENTRY', 'EMPLOYEE'],
    });

    expect(targets.map((t) => t.id)).toEqual(['departmental', 'portal']);
  });

  test('includes only departmental target for departmental-only authority', () => {
    const targets = buildSwitchTargets({
      isSystemAdmin: false,
      canDepartmentScopedPortal: true,
      hasDepartmentalAuthority: true,
      hasNonEmployeeAuthority: true,
      canAdminPortal: false,
      isGlobalRole: false,
      canEssPortal: false,
      essHomePath: '/ess/dashboard',
      authorities: ['DEPT_DATA_ENTRY'],
    });

    expect(targets.map((t) => t.id)).toEqual(['departmental']);
  });

  test('includes only global target for global non-department role', () => {
    const targets = buildSwitchTargets({
      isSystemAdmin: false,
      canDepartmentScopedPortal: false,
      hasDepartmentalAuthority: false,
      hasNonEmployeeAuthority: true,
      canAdminPortal: false,
      isGlobalRole: true,
      canEssPortal: false,
      essHomePath: '/ess/dashboard',
      authorities: ['GLOBAL_DATA_ENTRY'],
    });

    expect(targets.map((t) => t.id)).toEqual(['portal']);
  });

  test('treats dealing assistant as a global portal role', () => {
    const targets = buildSwitchTargets({
      isSystemAdmin: false,
      canDepartmentScopedPortal: false,
      hasDepartmentalAuthority: false,
      hasNonEmployeeAuthority: true,
      canAdminPortal: false,
      isGlobalRole: true,
      canEssPortal: false,
      essHomePath: '/ess/dashboard',
      authorities: ['DEALING_ASSISTANT'],
    });

    expect(targets.map((t) => t.id)).toEqual(['portal']);
  });

  test('includes ess target for employee-only users', () => {
    const targets = buildSwitchTargets({
      isSystemAdmin: false,
      canDepartmentScopedPortal: false,
      hasDepartmentalAuthority: false,
      hasNonEmployeeAuthority: false,
      canAdminPortal: false,
      isGlobalRole: false,
      canEssPortal: true,
      essHomePath: '/ess/profile',
      authorities: ['EMPLOYEE'],
    });

    expect(targets.map((t) => t.id)).toEqual(['ess']);
    expect(targets[0].path).toBe('/ess/profile');
  });

  test('shows ess and admin targets when admin portal is available', () => {
    const targets = buildSwitchTargets({
      isSystemAdmin: false,
      canDepartmentScopedPortal: false,
      hasDepartmentalAuthority: false,
      hasNonEmployeeAuthority: true,
      canAdminPortal: true,
      isGlobalRole: true,
      canEssPortal: true,
      essHomePath: '/ess/dashboard',
      authorities: ['SYSTEM_ADMIN', 'EMPLOYEE'],
    });

    expect(targets.map((t) => t.id)).toEqual(['ess', 'admin']);
  });

  test('returns no switch targets for system admin mode', () => {
    const targets = buildSwitchTargets({
      isSystemAdmin: true,
      canDepartmentScopedPortal: true,
      hasDepartmentalAuthority: true,
      hasNonEmployeeAuthority: true,
      canAdminPortal: true,
      isGlobalRole: true,
      canEssPortal: true,
      essHomePath: '/ess/dashboard',
      authorities: ['SYSTEM_ADMIN', 'GLOBAL_DATA_ENTRY', 'DEPT_DATA_ENTRY', 'EMPLOYEE'],
    });

    expect(targets).toEqual([]);
  });
});
