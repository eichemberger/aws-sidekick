<template>
  <div class="aws-account-manager">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white">AWS Accounts</h2>
        <p class="text-secondary mt-1">Manage your AWS account credentials</p>
      </div>
      <button
        @click="openRegisterModal"
        class="btn btn-primary"
      >
        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
        </svg>
        Add Account
      </button>
    </div>

    <!-- Error Display -->
    <div v-if="error" class="alert alert-error mb-4">
      <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
      </svg>
      <span>{{ error }}</span>
      <button @click="clearError" class="btn btn-sm btn-ghost ml-auto">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <!-- Active Account Display -->
    <div v-if="activeAccount" class="card bg-blue-50 dark:bg-blue-900/10 border border-blue-200 dark:border-blue-800 mb-6">
      <div class="card-body">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-lg font-semibold text-blue-700 dark:text-blue-300 flex items-center">
              <svg class="w-5 h-5 mr-2 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
              </svg>
              Active: {{ activeAccount.alias }}
            </h3>
            <p class="text-secondary text-sm">{{ activeAccount.description || 'No description' }}</p>
            <div class="flex items-center gap-4 mt-2 text-sm text-secondary">
              <span>{{ activeAccount.region }}</span>
              <span v-if="activeAccount.account_id">ID: {{ activeAccount.account_id }}</span>
              <span class="badge badge-sm" :class="activeAccount.uses_profile ? 'badge-info' : 'badge-secondary'">
                {{ activeAccount.uses_profile ? 'Profile' : 'Keys' }}
              </span>
            </div>
          </div>
          <button
            @click="clearActiveAccount"
            class="btn btn-sm btn-ghost"
            title="Clear active account"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading && !hasAccounts" class="flex justify-center py-8">
      <div class="loading loading-spinner loading-lg"></div>
    </div>

    <!-- Empty State -->
    <div v-else-if="!hasAccounts" class="card bg-gray-100 dark:bg-gray-800">
      <div class="card-body text-center py-12">
        <svg class="w-16 h-16 mx-auto text-secondary mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2V7zm0 0V5a2 2 0 012-2h6l2 2h6a2 2 0 012 2v2M7 13h10" />
        </svg>
        <h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-2">No AWS Accounts</h3>
        <p v-if="error && error.includes('404')" class="text-secondary mb-4">
          Multi-account features are not available yet. Please use the legacy AWS credentials setup.
        </p>
        <p v-else class="text-secondary mb-4">Register your first AWS account to get started</p>
        <button 
          v-if="!error || !error.includes('404')"
          @click="openRegisterModal" 
          class="btn btn-primary"
        >
          Add Your First Account
        </button>
      </div>
    </div>

    <!-- Accounts List -->
    <div v-else class="space-y-4">
      <div
        v-for="account in sortedAccounts"
        :key="account.alias"
        class="card bg-white dark:bg-gray-800 border hover:shadow-md transition-shadow"
        :class="{
          'border-blue-500 bg-blue-50 dark:bg-blue-900/10': account.alias === activeAccountAlias,
          'border-yellow-400 bg-yellow-50 dark:bg-yellow-900/10': account.is_default && account.alias !== activeAccountAlias
        }"
      >
        <div class="card-body">
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <div class="flex items-center gap-2 mb-2">
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ account.alias }}</h3>
                <div class="flex gap-1">
                  <span v-if="account.is_default" class="badge badge-warning badge-sm">Default</span>
                  <span v-if="account.alias === activeAccountAlias" class="badge badge-success badge-sm">Active</span>
                  <span class="badge badge-sm" :class="account.uses_profile ? 'badge-info' : 'badge-secondary'">
                    {{ account.uses_profile ? 'Profile' : 'Keys' }}
                  </span>
                </div>
              </div>
              
              <p v-if="account.description" class="text-secondary text-sm mb-2">{{ account.description }}</p>
              
              <div class="flex items-center gap-4 text-sm text-secondary">
                <span>{{ account.region }}</span>
                <span v-if="account.account_id">ID: {{ account.account_id }}</span>
                <span>Created: {{ formatDate(account.created_at) }}</span>
              </div>
            </div>

                        <!-- Account Actions -->
            <div class="flex items-center gap-2">
              <!-- Set Active Button -->
              <button
                v-if="account.alias !== activeAccountAlias"
                @click="setActiveAccount(account.alias)"
                class="btn btn-sm btn-outline btn-primary"
                :disabled="isLoading"
                title="Set as active account"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Activate
              </button>

              <!-- Dropdown Menu -->
              <div class="relative" :ref="`dropdown-${account.alias}`">
                <button 
                  @click="toggleDropdown(account.alias)"
                  class="btn btn-sm btn-ghost"
                  :class="{ 'bg-gray-100 dark:bg-gray-700': openDropdowns[account.alias] }"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01" />
                  </svg>
                </button>
                
                <!-- Dropdown Content -->
                <div 
                  v-if="openDropdowns[account.alias]"
                  class="absolute right-0 top-full mt-1 w-52 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50"
                >
                  <div class="py-1">
                    <button
                      v-if="!account.is_default"
                      @click="handleDropdownAction(() => setDefaultAccount(account.alias))"
                      class="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                      </svg>
                      Set as Default
                    </button>
                    <button
                      @click="handleDropdownAction(() => editAccount(account))"
                      class="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                      Edit Credentials
                    </button>
                    <div class="border-t border-gray-200 dark:border-gray-700 my-1"></div>
                    <button
                      @click="handleDropdownAction(() => deleteAccount(account.alias))"
                      class="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                      Delete Account
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Register Account Modal -->
    <div v-if="showRegisterForm" class="modal modal-open">
      <div class="modal-backdrop" @click="!isLoading && closeRegisterModal()"></div>
      <div class="modal-box w-11/12 max-w-2xl relative">
        <!-- Loading Overlay -->
        <div v-if="isLoading" class="absolute inset-0 bg-white/80 dark:bg-gray-900/80 flex items-center justify-center z-50 rounded-lg">
          <div class="text-center">
            <div class="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
            <p class="text-sm font-medium text-gray-700 dark:text-gray-300">Registering account...</p>
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">Please wait while we validate your credentials</p>
          </div>
        </div>

        <div class="flex items-center justify-between mb-4">
          <h3 class="font-bold text-lg">Register New AWS Account</h3>
          <button 
            @click="closeRegisterModal" 
            class="btn btn-sm btn-ghost"
            :disabled="isLoading"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <!-- Registration Form -->
        <form @submit.prevent="handleAccountRegistration" class="space-y-6">
          <!-- Account Details -->
          <div class="space-y-4">
            <h4 class="text-sm font-medium text-gray-900 dark:text-white">Account Details</h4>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Account Alias *
                </label>
                <input
                  v-model="registerForm.alias"
                  type="text"
                  class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                  :class="{ 
                    'border-red-300 dark:border-red-600 focus:ring-red-500': 
                      registerForm.showValidationErrors && !registerForm.alias?.trim() 
                  }"
                  placeholder="e.g., production, development"
                  required
                />
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Unique identifier for this AWS account
                </p>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Region *
                </label>
                <input
                  v-model="registerForm.credentials.region"
                  type="text"
                  readonly
                  class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                />
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  All accounts use us-east-1 region
                </p>
              </div>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Description
              </label>
              <textarea
                v-model="registerForm.description"
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                placeholder="Optional description for this account"
                rows="2"
              ></textarea>
            </div>
          </div>

          <!-- Credential Type Selector -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Authentication Method</label>
            <div class="flex flex-wrap gap-4">
              <label class="flex items-center cursor-pointer">
                <input
                  v-model="registerForm.authMethod"
                  type="radio"
                  value="sso-export"
                  class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 dark:border-gray-600"
                />
                <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">SSO Export</span>
              </label>
              <label class="flex items-center cursor-pointer">
                <input
                  v-model="registerForm.authMethod"
                  type="radio"
                  value="keys"
                  class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 dark:border-gray-600"
                />
                <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">Access Keys</span>
              </label>
              <label class="flex items-center cursor-pointer">
                <input
                  v-model="registerForm.authMethod"
                  type="radio"
                  value="profile"
                  class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 dark:border-gray-600"
                />
                <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">AWS Profile</span>
              </label>
            </div>
          </div>

          <!-- SSO Export Form -->
          <div v-if="registerForm.authMethod === 'sso-export'" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Paste AWS SSO Export Commands *
              </label>
              <textarea
                v-model="registerForm.ssoExportText"
                @input="parseRegisterSsoExport"
                rows="6"
                required
                placeholder="Paste the export commands from AWS SSO:&#10;export AWS_ACCESS_KEY_ID=&quot;...&quot;&#10;export AWS_SECRET_ACCESS_KEY=&quot;...&quot;&#10;export AWS_SESSION_TOKEN=&quot;...&quot;"
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 font-mono text-sm"
                :class="{ 
                  'border-red-300 dark:border-red-600 focus:ring-red-500': 
                    registerForm.showValidationErrors && (!registerForm.ssoExportText?.trim() || !registerForm.parsedSsoCredentials.access_key_id)
                }"
              />
              <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Copy and paste the export commands directly from AWS SSO or CLI
              </p>
            </div>
            
            <!-- Parsed Credentials Preview -->
            <div v-if="registerForm.parsedSsoCredentials.access_key_id" class="p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md">
              <h4 class="text-sm font-medium text-blue-800 dark:text-blue-300 mb-2">Parsed Credentials</h4>
              <div class="space-y-1 text-xs text-blue-700 dark:text-blue-200">
                <div class="flex">
                  <span class="font-medium w-32">Access Key ID:</span>
                  <span class="font-mono">{{ registerForm.parsedSsoCredentials.access_key_id.substring(0, 10) }}...</span>
                </div>
                <div class="flex">
                  <span class="font-medium w-32">Secret Key:</span>
                  <span class="font-mono">{{ registerForm.parsedSsoCredentials.secret_access_key ? '***' + registerForm.parsedSsoCredentials.secret_access_key.slice(-4) : 'Not found' }}</span>
                </div>
                <div class="flex">
                  <span class="font-medium w-32">Session Token:</span>
                  <span class="font-mono">{{ registerForm.parsedSsoCredentials.session_token ? '***' + registerForm.parsedSsoCredentials.session_token.slice(-4) : 'Not found' }}</span>
                </div>
              </div>
            </div>

            <!-- Parse Error -->
            <div v-if="registerForm.ssoParseError" class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
              <div class="flex">
                <svg class="h-5 w-5 text-red-600 dark:text-red-300 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div class="ml-2">
                  <p class="text-sm text-red-800 dark:text-red-300">{{ registerForm.ssoParseError }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Access Keys Form -->
          <div v-else-if="registerForm.authMethod === 'keys'" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Access Key ID *
              </label>
              <input
                v-model="registerForm.credentials.access_key_id"
                type="text"
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                :class="{ 
                  'border-red-300 dark:border-red-600 focus:ring-red-500': 
                    registerForm.showValidationErrors && !registerForm.credentials.access_key_id?.trim() 
                }"
                placeholder="AKIA..."
                required
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Secret Access Key *
              </label>
              <div class="relative">
                <input
                  v-model="registerForm.credentials.secret_access_key"
                  :type="registerForm.showSecretKey ? 'text' : 'password'"
                  class="w-full px-3 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                  :class="{ 
                    'border-red-300 dark:border-red-600 focus:ring-red-500': 
                      registerForm.showValidationErrors && !registerForm.credentials.secret_access_key?.trim() 
                  }"
                  placeholder="••••••••••••••••••••••••••••••••••••••••"
                  required
                />
                <button
                  type="button"
                  @click="registerForm.showSecretKey = !registerForm.showSecretKey"
                  class="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                >
                  <svg v-if="registerForm.showSecretKey" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L12 12m0 0l3.878 3.878M3 3l18 18" />
                  </svg>
                  <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                </button>
              </div>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Session Token
              </label>
              <input
                v-model="registerForm.credentials.session_token"
                type="text"
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                placeholder="Optional session token"
              />
            </div>
          </div>

          <!-- AWS Profile -->
          <div v-else-if="registerForm.authMethod === 'profile'">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              AWS Profile Name *
            </label>
            <input
              v-model="registerForm.credentials.profile"
              type="text"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
              :class="{ 
                'border-red-300 dark:border-red-600 focus:ring-red-500': 
                  registerForm.showValidationErrors && !registerForm.credentials.profile?.trim() 
              }"
              placeholder="default"
              required
            />
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Profile name from ~/.aws/credentials or ~/.aws/config
            </p>
          </div>

          <!-- Options -->
          <div class="flex items-center gap-4">
            <label class="cursor-pointer flex items-center gap-2">
              <input
                v-model="registerForm.setAsDefault"
                type="checkbox"
                class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 dark:border-gray-600 rounded"
              />
              <span class="text-sm text-gray-700 dark:text-gray-300">Set as default account</span>
            </label>
          </div>

          <!-- Validation Errors Display -->
          <div v-if="registerForm.showValidationErrors && registerValidationMessages.length > 0" class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
            <div class="flex">
              <svg class="h-5 w-5 text-red-600 dark:text-red-300 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div class="ml-2">
                <p class="text-sm font-medium text-red-800 dark:text-red-300 mb-2">Please fix the following issues:</p>
                <ul class="text-sm text-red-700 dark:text-red-200 space-y-1">
                  <li v-for="message in registerValidationMessages" :key="message" class="flex items-start">
                    <span class="mr-2">•</span>
                    <span>{{ message }}</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex justify-end gap-2 pt-4">
            <button
              type="button"
              @click="closeRegisterModal"
              class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              :disabled="isLoading"
            >
              Cancel
            </button>
            <button
              type="button"
              @click="validateRegisterCredentials"
              class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              :disabled="isLoading || registerForm.isValidating"
            >
              <span v-if="registerForm.isValidating" class="flex items-center">
                <svg class="w-4 h-4 animate-spin mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Validating...
              </span>
              <span v-else>Validate</span>
            </button>
            <button
              type="submit"
              class="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              :disabled="isLoading || registerForm.isValidating"
            >
              <span v-if="isLoading" class="flex items-center">
                <svg class="w-4 h-4 animate-spin mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Registering...
              </span>
              <span v-else>Register Account</span>
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Edit Account Modal -->
    <div v-if="showEditForm && editingAccount" class="modal modal-open">
      <div class="modal-backdrop" @click="!isLoading && cancelEdit()"></div>
      <div class="modal-box w-11/12 max-w-2xl relative">
        <!-- Loading Overlay -->
        <div v-if="isLoading" class="absolute inset-0 bg-white/80 dark:bg-gray-900/80 flex items-center justify-center z-50 rounded-lg">
          <div class="text-center">
            <div class="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
            <p class="text-sm font-medium text-gray-700 dark:text-gray-300">Updating account credentials...</p>
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">Please wait while we validate your credentials</p>
          </div>
        </div>

        <div class="flex items-center justify-between mb-4">
          <h3 class="font-bold text-lg">Edit Account: {{ editingAccount.alias }}</h3>
          <button 
            @click="cancelEdit" 
            class="btn btn-sm btn-ghost"
            :disabled="isLoading"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <!-- Edit Form -->
        <form @submit.prevent="handleAccountUpdate" class="space-y-6">
          <!-- Account Details (Read-only) -->
          <div class="space-y-4">
            <h4 class="text-sm font-medium text-gray-900 dark:text-white">Account Details</h4>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Account Alias
                </label>
                <input
                  :value="editingAccount.alias"
                  type="text"
                  class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                  readonly
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Region *
                </label>
                <input
                  v-model="editForm.credentials.region"
                  type="text"
                  readonly
                  class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                />
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  All accounts use us-east-1 region
                </p>
              </div>
            </div>
          </div>

          <!-- Credential Type Selector -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Authentication Method</label>
            <div class="flex flex-wrap gap-4">
              <label class="flex items-center cursor-pointer">
                <input
                  v-model="editForm.authMethod"
                  type="radio"
                  value="sso-export"
                  class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 dark:border-gray-600"
                />
                <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">SSO Export</span>
              </label>
              <label class="flex items-center cursor-pointer">
                <input
                  v-model="editForm.authMethod"
                  type="radio"
                  value="keys"
                  class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 dark:border-gray-600"
                />
                <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">Access Keys</span>
              </label>
              <label class="flex items-center cursor-pointer">
                <input
                  v-model="editForm.authMethod"
                  type="radio"
                  value="profile"
                  class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 dark:border-gray-600"
                />
                <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">AWS Profile</span>
              </label>
            </div>
          </div>

          <!-- SSO Export Form -->
          <div v-if="editForm.authMethod === 'sso-export'" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Paste AWS SSO Export Commands *
              </label>
              <textarea
                v-model="editForm.ssoExportText"
                @input="parseEditSsoExport"
                rows="6"
                required
                placeholder="Paste the export commands from AWS SSO:&#10;export AWS_ACCESS_KEY_ID=&quot;...&quot;&#10;export AWS_SECRET_ACCESS_KEY=&quot;...&quot;&#10;export AWS_SESSION_TOKEN=&quot;...&quot;"
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 font-mono text-sm"
                :class="{ 
                  'border-red-300 dark:border-red-600 focus:ring-red-500': 
                    editForm.showValidationErrors && (!editForm.ssoExportText?.trim() || !editForm.parsedSsoCredentials.access_key_id)
                }"
              />
              <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Copy and paste the export commands directly from AWS SSO or CLI
              </p>
            </div>
            
            <!-- Parsed Credentials Preview -->
            <div v-if="editForm.parsedSsoCredentials.access_key_id" class="p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md">
              <h4 class="text-sm font-medium text-blue-800 dark:text-blue-300 mb-2">Parsed Credentials</h4>
              <div class="space-y-1 text-xs text-blue-700 dark:text-blue-200">
                <div class="flex">
                  <span class="font-medium w-32">Access Key ID:</span>
                  <span class="font-mono">{{ editForm.parsedSsoCredentials.access_key_id.substring(0, 10) }}...</span>
                </div>
                <div class="flex">
                  <span class="font-medium w-32">Secret Key:</span>
                  <span class="font-mono">{{ editForm.parsedSsoCredentials.secret_access_key ? '***' + editForm.parsedSsoCredentials.secret_access_key.slice(-4) : 'Not found' }}</span>
                </div>
                <div class="flex">
                  <span class="font-medium w-32">Session Token:</span>
                  <span class="font-mono">{{ editForm.parsedSsoCredentials.session_token ? '***' + editForm.parsedSsoCredentials.session_token.slice(-4) : 'Not found' }}</span>
                </div>
              </div>
            </div>

            <!-- Parse Error -->
            <div v-if="editForm.ssoParseError" class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
              <div class="flex">
                <svg class="h-5 w-5 text-red-600 dark:text-red-300 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div class="ml-2">
                  <p class="text-sm text-red-800 dark:text-red-300">{{ editForm.ssoParseError }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Access Keys Form -->
          <div v-else-if="editForm.authMethod === 'keys'" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Access Key ID *
              </label>
              <input
                v-model="editForm.credentials.access_key_id"
                type="text"
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                :class="{ 
                  'border-red-300 dark:border-red-600 focus:ring-red-500': 
                    editForm.showValidationErrors && !editForm.credentials.access_key_id?.trim() 
                }"
                placeholder="AKIA..."
                required
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Secret Access Key *
              </label>
              <div class="relative">
                <input
                  v-model="editForm.credentials.secret_access_key"
                  :type="editForm.showSecretKey ? 'text' : 'password'"
                  class="w-full px-3 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                  :class="{ 
                    'border-red-300 dark:border-red-600 focus:ring-red-500': 
                      editForm.showValidationErrors && !editForm.credentials.secret_access_key?.trim() 
                  }"
                  placeholder="••••••••••••••••••••••••••••••••••••••••"
                  required
                />
                <button
                  type="button"
                  @click="editForm.showSecretKey = !editForm.showSecretKey"
                  class="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                >
                  <svg v-if="editForm.showSecretKey" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L12 12m0 0l3.878 3.878M3 3l18 18" />
                  </svg>
                  <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                </button>
              </div>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Session Token
              </label>
              <input
                v-model="editForm.credentials.session_token"
                type="text"
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                placeholder="Optional session token"
              />
            </div>
          </div>

          <!-- AWS Profile -->
          <div v-else-if="editForm.authMethod === 'profile'">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              AWS Profile Name *
            </label>
            <input
              v-model="editForm.credentials.profile"
              type="text"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
              :class="{ 
                'border-red-300 dark:border-red-600 focus:ring-red-500': 
                  editForm.showValidationErrors && !editForm.credentials.profile?.trim() 
              }"
              placeholder="default"
              required
            />
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Profile name from ~/.aws/credentials or ~/.aws/config
            </p>
          </div>

          <!-- Validation Errors Display -->
          <div v-if="editForm.showValidationErrors && editValidationMessages.length > 0" class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
            <div class="flex">
              <svg class="h-5 w-5 text-red-600 dark:text-red-300 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div class="ml-2">
                <p class="text-sm font-medium text-red-800 dark:text-red-300 mb-2">Please fix the following issues:</p>
                <ul class="text-sm text-red-700 dark:text-red-200 space-y-1">
                  <li v-for="message in editValidationMessages" :key="message" class="flex items-start">
                    <span class="mr-2">•</span>
                    <span>{{ message }}</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex justify-end gap-2 pt-4">
            <button
              type="button"
              @click="cancelEdit"
              class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              :disabled="isLoading"
            >
              Cancel
            </button>
            <button
              type="button"
              @click="validateEditCredentials"
              class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              :disabled="isLoading || editForm.isValidating"
            >
              <span v-if="editForm.isValidating" class="flex items-center">
                <svg class="w-4 h-4 animate-spin mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Validating...
              </span>
              <span v-else>Validate</span>
            </button>
            <button
              type="submit"
              class="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              :disabled="isLoading || editForm.isValidating"
            >
              <span v-if="isLoading" class="flex items-center">
                <svg class="w-4 h-4 animate-spin mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Updating...
              </span>
              <span v-else>Update Credentials</span>
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div v-if="showDeleteConfirm && deletingAccount" class="modal modal-open">
      <div class="modal-backdrop" @click="cancelDelete"></div>
      <div class="modal-box">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-bold text-lg text-red-600 dark:text-red-400">Delete Account</h3>
          <button @click="cancelDelete" class="btn btn-sm btn-ghost">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <p class="mb-6">
          Are you sure you want to delete the AWS account <strong>{{ deletingAccount }}</strong>?
          This action cannot be undone.
        </p>
        
        <div class="flex justify-end gap-2">
          <button @click="cancelDelete" class="btn btn-ghost">Cancel</button>
          <button @click="confirmDelete" class="btn btn-error" :disabled="isLoading">
            <span v-if="isLoading" class="loading loading-spinner loading-sm"></span>
            Delete Account
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, reactive, computed } from 'vue'
import { useAwsAccountsStore } from '@/stores/awsAccounts'
// import AWSCredentialsManager from './AWSCredentialsManager.vue'
import type { AWSAccount, AWSCredentialsRequest } from '@/types/api'
import { storeToRefs } from 'pinia'

// Store
const accountsStore = useAwsAccountsStore()
const {
  accounts,
  activeAccount,
  activeAccountAlias,
  sortedAccounts,
  hasAccounts,
  isLoading,
  error
} = storeToRefs(accountsStore)

// Local state
const showRegisterForm = ref(false)
const showEditForm = ref(false)
const editingAccount = ref<AWSAccount | null>(null)
const showDeleteConfirm = ref(false)
const deletingAccount = ref<string | null>(null)
const openDropdowns = reactive<Record<string, boolean>>({})

// Form data
const registerForm = reactive({
  alias: '',
  description: '',
  credentials: {
    access_key_id: '',
    secret_access_key: '',
    session_token: '',
    region: 'us-east-1',
    profile: ''
  },
  authMethod: 'sso-export',
  setAsDefault: false,
  showSecretKey: false,
  ssoExportText: '',
  parsedSsoCredentials: {
    access_key_id: '',
    secret_access_key: '',
    session_token: ''
  },
  ssoParseError: null as string | null,
  showValidationErrors: false,
  isValidating: false
})

const editForm = reactive({
  credentials: {
    access_key_id: '',
    secret_access_key: '',
    session_token: '',
    region: 'us-east-1',
    profile: ''
  },
  authMethod: 'sso-export',
  showSecretKey: false,
  ssoExportText: '',
  parsedSsoCredentials: {
    access_key_id: '',
    secret_access_key: '',
    session_token: ''
  },
  ssoParseError: null as string | null,
  showValidationErrors: false,
  isValidating: false
})

// Computed properties
const registerValidationMessages = computed(() => {
  const messages: string[] = []
  
  if (!registerForm.alias?.trim()) {
    messages.push('Account alias is required')
  } else if (!/^[a-zA-Z0-9-_]+$/.test(registerForm.alias.trim())) {
    messages.push('Account alias can only contain letters, numbers, hyphens, and underscores')
  }
  
  if (registerForm.authMethod === 'keys') {
    if (!registerForm.credentials.access_key_id?.trim()) {
      messages.push('Access Key ID is required')
    }
    if (!registerForm.credentials.secret_access_key?.trim()) {
      messages.push('Secret Access Key is required')
    }
  } else if (registerForm.authMethod === 'profile') {
    if (!registerForm.credentials.profile?.trim()) {
      messages.push('AWS Profile name is required')
    }
  } else if (registerForm.authMethod === 'sso-export') {
    if (!registerForm.ssoExportText?.trim()) {
      messages.push('Please paste AWS SSO export commands')
    } else if (!registerForm.parsedSsoCredentials.access_key_id) {
      messages.push('Could not find AWS_ACCESS_KEY_ID in export commands')
    } else if (!registerForm.parsedSsoCredentials.secret_access_key) {
      messages.push('Could not find AWS_SECRET_ACCESS_KEY in export commands')
    }
  }
  
  return messages
})

const editValidationMessages = computed(() => {
  const messages: string[] = []
  
  if (editForm.authMethod === 'keys') {
    if (!editForm.credentials.access_key_id?.trim()) {
      messages.push('Access Key ID is required')
    }
    if (!editForm.credentials.secret_access_key?.trim()) {
      messages.push('Secret Access Key is required')
    }
  } else if (editForm.authMethod === 'profile') {
    if (!editForm.credentials.profile?.trim()) {
      messages.push('AWS Profile name is required')
    }
  } else if (editForm.authMethod === 'sso-export') {
    if (!editForm.ssoExportText?.trim()) {
      messages.push('Please paste AWS SSO export commands')
    } else if (!editForm.parsedSsoCredentials.access_key_id) {
      messages.push('Could not find AWS_ACCESS_KEY_ID in export commands')
    } else if (!editForm.parsedSsoCredentials.secret_access_key) {
      messages.push('Could not find AWS_SECRET_ACCESS_KEY in export commands')
    }
  }
  
  return messages
})

// Methods
const clearError = () => {
  accountsStore.clearError()
}

const openRegisterModal = () => {
  resetRegisterForm()
  showRegisterForm.value = true
}

const closeRegisterModal = () => {
  showRegisterForm.value = false
  resetRegisterForm()
}

const resetRegisterForm = () => {
  registerForm.alias = ''
  registerForm.description = ''
  registerForm.credentials.access_key_id = ''
  registerForm.credentials.secret_access_key = ''
  registerForm.credentials.session_token = ''
  registerForm.credentials.region = 'us-east-1'
  registerForm.credentials.profile = ''
  registerForm.authMethod = 'sso-export'
  registerForm.setAsDefault = false
  registerForm.showSecretKey = false
  registerForm.ssoExportText = ''
  registerForm.parsedSsoCredentials = {
    access_key_id: '',
    secret_access_key: '',
    session_token: ''
  }
  registerForm.ssoParseError = null
  registerForm.showValidationErrors = false
  registerForm.isValidating = false
}

const resetEditForm = () => {
  editForm.credentials.access_key_id = ''
  editForm.credentials.secret_access_key = ''
  editForm.credentials.session_token = ''
  editForm.credentials.region = 'us-east-1'
  editForm.credentials.profile = ''
  editForm.authMethod = 'sso-export'
  editForm.showSecretKey = false
  editForm.ssoExportText = ''
  editForm.parsedSsoCredentials = {
    access_key_id: '',
    secret_access_key: '',
    session_token: ''
  }
  editForm.ssoParseError = null
  editForm.showValidationErrors = false
  editForm.isValidating = false
}

const setActiveAccount = async (alias: string) => {
  try {
    await accountsStore.setActiveAccount(alias)
  } catch (err) {
    console.error('Failed to set active account:', err)
  }
}

const clearActiveAccount = async () => {
  try {
    await accountsStore.clearActiveAccount()
  } catch (err) {
    console.error('Failed to clear active account:', err)
  }
}

const setDefaultAccount = async (alias: string) => {
  try {
    await accountsStore.setDefaultAccount(alias)
  } catch (err) {
    console.error('Failed to set default account:', err)
  }
}

const handleAccountRegistration = async () => {
  // Validate form before submission
  if (registerValidationMessages.value.length > 0) {
    registerForm.showValidationErrors = true
    return
  }

  registerForm.showValidationErrors = false
  
  if (!registerForm.alias || !registerForm.credentials.region) {
    console.error('Alias and region are required for account registration')
    return
  }
  
  try {
    // Create credentials object based on auth method
    const credentials = createRegisterCredentialsObject()
    
    await accountsStore.registerAccount({
      alias: registerForm.alias,
      credentials,
      description: registerForm.description || undefined,
      set_as_default: registerForm.setAsDefault
    })
    
    closeRegisterModal()
  } catch (err) {
    console.error('Failed to register account:', err)
  }
}

const editAccount = (account: AWSAccount) => {
  editingAccount.value = account
  // Initialize form with current account data
  editForm.credentials.region = account.region
  editForm.authMethod = account.uses_profile ? 'profile' : 'keys'
  showEditForm.value = true
}

const handleAccountUpdate = async () => {
  if (!editingAccount.value) {
    console.error('No account selected for editing')
    return
  }
  
  if (editValidationMessages.value.length > 0) {
    editForm.showValidationErrors = true
    return
  }
  
  editForm.showValidationErrors = false
  isLoading.value = true
  
  try {
    // Create credentials object based on auth method
    const credentials = createEditCredentialsObject()
    
    await accountsStore.updateAccountCredentials(editingAccount.value.alias, credentials)
    cancelEdit()
  } catch (err) {
    console.error('Failed to update account:', err)
  } finally {
    isLoading.value = false
  }
}

const cancelEdit = () => {
  editingAccount.value = null
  showEditForm.value = false
  resetEditForm()
}

const deleteAccount = (alias: string) => {
  deletingAccount.value = alias
  showDeleteConfirm.value = true
}

const confirmDelete = async () => {
  if (!deletingAccount.value) return
  
  try {
    await accountsStore.deleteAccount(deletingAccount.value)
    cancelDelete()
  } catch (err) {
    console.error('Failed to delete account:', err)
  }
}

const cancelDelete = () => {
  deletingAccount.value = null
  showDeleteConfirm.value = false
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString()
}

// Dropdown management
const toggleDropdown = (alias: string) => {
  // Close all other dropdowns
  Object.keys(openDropdowns).forEach(key => {
    if (key !== alias) {
      openDropdowns[key] = false
    }
  })
  // Toggle current dropdown
  openDropdowns[alias] = !openDropdowns[alias]
}

const closeAllDropdowns = () => {
  Object.keys(openDropdowns).forEach(key => {
    openDropdowns[key] = false
  })
}

const handleDropdownAction = (action: () => void) => {
  action()
  closeAllDropdowns()
}

// Click outside handler
const handleClickOutside = (event: Event) => {
  const target = event.target as HTMLElement
  if (!target.closest('.relative')) {
    closeAllDropdowns()
  }
}

const parseRegisterSsoExport = () => {
  registerForm.ssoParseError = null
  registerForm.parsedSsoCredentials = { access_key_id: '', secret_access_key: '', session_token: '' }

  if (!registerForm.ssoExportText.trim()) return

  try {
    const lines = registerForm.ssoExportText.split('\n')
    
    for (const line of lines) {
      const trimmedLine = line.trim()
      
      // Skip empty lines and comments
      if (!trimmedLine || trimmedLine.startsWith('#')) continue
      
      // Match export AWS_ACCESS_KEY_ID="value" or export AWS_ACCESS_KEY_ID=value
      // Also handle cases without 'export' prefix
      const accessKeyMatch = trimmedLine.match(/(?:export\s+)?AWS_ACCESS_KEY_ID\s*=\s*["']?([^"'\s]+)["']?/)
      if (accessKeyMatch) {
        registerForm.parsedSsoCredentials.access_key_id = accessKeyMatch[1]
        continue
      }
      
      // Match export AWS_SECRET_ACCESS_KEY="value" or export AWS_SECRET_ACCESS_KEY=value
      const secretKeyMatch = trimmedLine.match(/(?:export\s+)?AWS_SECRET_ACCESS_KEY\s*=\s*["']?([^"'\s]+)["']?/)
      if (secretKeyMatch) {
        registerForm.parsedSsoCredentials.secret_access_key = secretKeyMatch[1]
        continue
      }
      
      // Match export AWS_SESSION_TOKEN="value" or export AWS_SESSION_TOKEN=value
      const sessionTokenMatch = trimmedLine.match(/(?:export\s+)?AWS_SESSION_TOKEN\s*=\s*["']?([^"'\s]+)["']?/)
      if (sessionTokenMatch) {
        registerForm.parsedSsoCredentials.session_token = sessionTokenMatch[1]
        continue
      }
    }
    
    // Validate that we got the required credentials
    if (!registerForm.parsedSsoCredentials.access_key_id) {
      registerForm.ssoParseError = 'AWS_ACCESS_KEY_ID not found in the export commands'
    } else if (!registerForm.parsedSsoCredentials.secret_access_key) {
      registerForm.ssoParseError = 'AWS_SECRET_ACCESS_KEY not found in the export commands'
    }
    
  } catch (error) {
    registerForm.ssoParseError = 'Failed to parse export commands. Please check the format.'
  }
}

const validateRegisterCredentials = async () => {
  if (registerValidationMessages.value.length > 0) {
    registerForm.showValidationErrors = true
    return
  }

  registerForm.showValidationErrors = false
  registerForm.isValidating = true

  try {
    // Create credentials object based on auth method
    const credentials = createRegisterCredentialsObject()
    
    // Here you would validate with your API
    // For now, just simulate validation
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    console.log('Credentials validated successfully:', credentials)
  } catch (err) {
    console.error('Failed to validate credentials:', err)
  } finally {
    registerForm.isValidating = false
  }
}

const createRegisterCredentialsObject = (): AWSCredentialsRequest => {
  if (registerForm.authMethod === 'keys') {
    return {
      access_key_id: registerForm.credentials.access_key_id,
      secret_access_key: registerForm.credentials.secret_access_key,
      session_token: registerForm.credentials.session_token || undefined,
      region: registerForm.credentials.region,
      profile: undefined
    }
  } else if (registerForm.authMethod === 'profile') {
    return {
      access_key_id: undefined,
      secret_access_key: undefined,
      session_token: undefined,
      region: registerForm.credentials.region,
      profile: registerForm.credentials.profile
    }
  } else if (registerForm.authMethod === 'sso-export') {
    return {
      access_key_id: registerForm.parsedSsoCredentials.access_key_id,
      secret_access_key: registerForm.parsedSsoCredentials.secret_access_key,
      session_token: registerForm.parsedSsoCredentials.session_token || undefined,
      region: registerForm.credentials.region,
      profile: undefined
    }
  }
  
  throw new Error('Invalid credential type')
}

const parseEditSsoExport = () => {
  editForm.ssoParseError = null
  editForm.parsedSsoCredentials = { access_key_id: '', secret_access_key: '', session_token: '' }

  if (!editForm.ssoExportText.trim()) return

  try {
    const lines = editForm.ssoExportText.split('\n')
    
    for (const line of lines) {
      const trimmedLine = line.trim()
      
      // Skip empty lines and comments
      if (!trimmedLine || trimmedLine.startsWith('#')) continue
      
      // Match export AWS_ACCESS_KEY_ID="value" or export AWS_ACCESS_KEY_ID=value
      // Also handle cases without 'export' prefix
      const accessKeyMatch = trimmedLine.match(/(?:export\s+)?AWS_ACCESS_KEY_ID\s*=\s*["']?([^"'\s]+)["']?/)
      if (accessKeyMatch) {
        editForm.parsedSsoCredentials.access_key_id = accessKeyMatch[1]
        continue
      }
      
      // Match export AWS_SECRET_ACCESS_KEY="value" or export AWS_SECRET_ACCESS_KEY=value
      const secretKeyMatch = trimmedLine.match(/(?:export\s+)?AWS_SECRET_ACCESS_KEY\s*=\s*["']?([^"'\s]+)["']?/)
      if (secretKeyMatch) {
        editForm.parsedSsoCredentials.secret_access_key = secretKeyMatch[1]
        continue
      }
      
      // Match export AWS_SESSION_TOKEN="value" or export AWS_SESSION_TOKEN=value
      const sessionTokenMatch = trimmedLine.match(/(?:export\s+)?AWS_SESSION_TOKEN\s*=\s*["']?([^"'\s]+)["']?/)
      if (sessionTokenMatch) {
        editForm.parsedSsoCredentials.session_token = sessionTokenMatch[1]
        continue
      }
    }
    
    // Validate that we got the required credentials
    if (!editForm.parsedSsoCredentials.access_key_id) {
      editForm.ssoParseError = 'AWS_ACCESS_KEY_ID not found in the export commands'
    } else if (!editForm.parsedSsoCredentials.secret_access_key) {
      editForm.ssoParseError = 'AWS_SECRET_ACCESS_KEY not found in the export commands'
    }
    
  } catch (error) {
    editForm.ssoParseError = 'Failed to parse export commands. Please check the format.'
  }
}

const validateEditCredentials = async () => {
  if (editValidationMessages.value.length > 0) {
    editForm.showValidationErrors = true
    return
  }

  editForm.showValidationErrors = false
  editForm.isValidating = true

  try {
    // Create credentials object based on auth method
    const credentials = createEditCredentialsObject()
    
    // Here you would validate with your API
    // For now, just simulate validation
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    console.log('Edit credentials validated successfully:', credentials)
  } catch (err) {
    console.error('Failed to validate credentials:', err)
  } finally {
    editForm.isValidating = false
  }
}

const createEditCredentialsObject = (): AWSCredentialsRequest => {
  if (editForm.authMethod === 'keys') {
    return {
      access_key_id: editForm.credentials.access_key_id,
      secret_access_key: editForm.credentials.secret_access_key,
      session_token: editForm.credentials.session_token || undefined,
      region: editForm.credentials.region,
      profile: undefined
    }
  } else if (editForm.authMethod === 'profile') {
    return {
      access_key_id: undefined,
      secret_access_key: undefined,
      session_token: undefined,
      region: editForm.credentials.region,
      profile: editForm.credentials.profile
    }
  } else if (editForm.authMethod === 'sso-export') {
    return {
      access_key_id: editForm.parsedSsoCredentials.access_key_id,
      secret_access_key: editForm.parsedSsoCredentials.secret_access_key,
      session_token: editForm.parsedSsoCredentials.session_token || undefined,
      region: editForm.credentials.region,
      profile: undefined
    }
  }
  
  throw new Error('Invalid credential type')
}

// Lifecycle
onMounted(async () => {
  await accountsStore.initialize()
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.aws-account-manager {
  @apply p-6 max-w-4xl mx-auto;
}

.alert {
  @apply flex items-center gap-3 p-4 rounded-lg;
}

.alert-error {
  @apply bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800;
}

.btn {
  @apply inline-flex items-center justify-center px-4 py-2 rounded-lg font-medium transition-colors;
}

.btn-primary {
  @apply bg-blue-600 text-white hover:bg-blue-700;
}

.btn-outline {
  @apply border border-current bg-transparent hover:bg-current hover:text-current;
}

.btn-ghost {
  @apply bg-transparent hover:bg-gray-100 dark:hover:bg-gray-700;
}

.btn-error {
  @apply bg-red-600 text-white hover:bg-red-700;
}

.btn-sm {
  @apply px-3 py-1 text-sm;
}

.btn:disabled {
  @apply opacity-50 cursor-not-allowed;
}

.card {
  @apply bg-white dark:bg-gray-800 rounded-lg;
}

.card-body {
  @apply p-6;
}

.badge {
  @apply inline-flex items-center px-2 py-1 rounded-full text-xs font-medium;
}

.badge-warning {
  @apply bg-yellow-100 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-300;
}

.badge-success {
  @apply bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-300;
}

.badge-info {
  @apply bg-blue-100 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300;
}

.badge-secondary {
  @apply bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300;
}

.badge-sm {
  @apply px-1.5 py-0.5 text-xs;
}

.modal {
  @apply fixed inset-0 z-50 flex items-center justify-center pointer-events-none;
}

.modal-open {
  @apply visible opacity-100 pointer-events-auto;
}

.modal-box {
  @apply relative z-10 bg-white dark:bg-gray-800 p-6 rounded-lg shadow-xl max-h-[90vh] overflow-y-auto;
}

.modal-backdrop {
  @apply absolute inset-0 bg-black/50 z-0 cursor-pointer;
}

.dropdown {
  @apply relative;
}

.dropdown-content {
  @apply absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-20;
}

.menu {
  @apply py-1;
}

.menu li a {
  @apply flex items-center gap-2 px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer;
}

.loading {
  @apply animate-spin;
}

.loading-spinner {
  @apply w-4 h-4 border-2 border-current border-t-transparent rounded-full;
}

.loading-lg {
  @apply w-8 h-8;
}

.loading-sm {
  @apply w-3 h-3;
}
</style> 