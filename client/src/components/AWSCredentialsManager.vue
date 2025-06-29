<template>
  <div class="card">
    <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-lg font-medium text-primary">AWS Credentials</h3>
          <p class="text-sm text-secondary">Configure AWS credentials for your session</p>
        </div>
        <div class="flex items-center space-x-2">
          <div v-if="awsStore.hasValidCredentials" class="flex items-center text-green-600 dark:text-green-400">
            <CheckCircleIcon class="h-5 w-5 mr-1" />
            <span class="text-sm font-medium">Connected</span>
          </div>
          <div v-else-if="awsStore.credentialsInfo && !awsStore.hasValidCredentials" class="flex items-center text-red-600 dark:text-red-400">
            <XCircleIcon class="h-5 w-5 mr-1" />
            <span class="text-sm font-medium">Invalid</span>
          </div>
          <div v-else class="flex items-center text-gray-500 dark:text-gray-500">
            <ExclamationTriangleIcon class="h-5 w-5 mr-1" />
            <span class="text-sm font-medium">Not configured</span>
          </div>
        </div>
      </div>
    </div>

    <div class="p-6">
      <!-- Current Account Info -->
      <div v-if="awsStore.accountInfo" class="mb-6 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
        <h4 class="text-sm font-medium text-green-800 dark:text-green-300 mb-2">Current AWS Account</h4>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <span class="text-green-700 dark:text-green-400 font-medium">Account ID:</span>
            <span class="text-green-600 dark:text-green-200 ml-1">{{ awsStore.accountId }}</span>
          </div>
          <div>
            <span class="text-green-700 dark:text-green-400 font-medium">Region:</span>
            <span class="text-green-600 dark:text-green-200 ml-1">{{ awsStore.region }}</span>
          </div>
          <div>
            <span class="text-green-700 dark:text-green-400 font-medium">Type:</span>
            <span class="text-green-600 dark:text-green-200 ml-1 capitalize">{{ awsStore.credentialsType }}</span>
          </div>
        </div>
      </div>

      <!-- Credential Type Selector -->
      <div class="mb-6">
        <label class="text-sm font-medium text-primary mb-3 block">Credential Type</label>
        <div class="flex space-x-4">
          <label class="flex items-center">
            <input
              v-model="credentialType"
              type="radio"
              value="keys"
              class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800"
            />
            <span class="ml-2 text-sm text-secondary">Access Keys</span>
          </label>
          <label class="flex items-center">
            <input
              v-model="credentialType"
              type="radio"
              value="profile"
              class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800"
            />
            <span class="ml-2 text-sm text-secondary">AWS Profile</span>
          </label>
        </div>
      </div>

      <!-- Credentials Form -->
      <form @submit.prevent="handleSubmit" class="space-y-4">
        <!-- Access Keys Form -->
        <div v-if="credentialType === 'keys'" class="space-y-4">
          <div>
            <label for="accessKeyId" class="block text-sm font-medium text-primary mb-1">
              Access Key ID *
            </label>
            <input
              id="accessKeyId"
              v-model="form.access_key_id"
              type="text"
              required
              placeholder="AKIAIOSFODNN7EXAMPLE"
              class="input-field"
            />
          </div>
          
          <div>
            <label for="secretAccessKey" class="block text-sm font-medium text-primary mb-1">
              Secret Access Key *
            </label>
            <input
              id="secretAccessKey"
              v-model="form.secret_access_key"
              type="password"
              required
              placeholder="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
              class="input-field"
            />
          </div>
          
          <div>
            <label for="sessionToken" class="block text-sm font-medium text-primary mb-1">
              Session Token (Optional)
            </label>
            <input
              id="sessionToken"
              v-model="form.session_token"
              type="password"
              placeholder="Temporary session token for assumed roles"
              class="input-field"
            />
          </div>
        </div>

        <!-- Profile Form -->
        <div v-else-if="credentialType === 'profile'" class="space-y-4">
          <div>
            <label for="profile" class="block text-sm font-medium text-primary mb-1">
              AWS Profile Name *
            </label>
            <input
              id="profile"
              v-model="form.profile"
              type="text"
              required
              placeholder="default"
              class="input-field"
            />
            <p class="text-xs text-muted mt-1">
              Profile name from ~/.aws/credentials or ~/.aws/config
            </p>
          </div>
        </div>

        <!-- Region -->
        <div>
          <label for="region" class="block text-sm font-medium text-primary mb-1">
            AWS Region *
          </label>
          <select
            id="region"
            v-model="form.region"
            required
            class="input-field"
          >
            <option value="us-east-1">US East (N. Virginia)</option>
            <option value="us-east-2">US East (Ohio)</option>
            <option value="us-west-1">US West (N. California)</option>
            <option value="us-west-2">US West (Oregon)</option>
            <option value="eu-west-1">Europe (Ireland)</option>
            <option value="eu-west-2">Europe (London)</option>
            <option value="eu-west-3">Europe (Paris)</option>
            <option value="eu-central-1">Europe (Frankfurt)</option>
            <option value="ap-southeast-1">Asia Pacific (Singapore)</option>
            <option value="ap-southeast-2">Asia Pacific (Sydney)</option>
            <option value="ap-northeast-1">Asia Pacific (Tokyo)</option>
            <option value="ap-south-1">Asia Pacific (Mumbai)</option>
            <option value="sa-east-1">South America (São Paulo)</option>
          </select>
        </div>

        <!-- Error Display -->
        <div v-if="error" class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
          <div class="flex">
            <XCircleIcon class="h-5 w-5 text-red-600 dark:text-red-300 flex-shrink-0" />
            <div class="ml-2">
              <p class="text-sm text-red-800 dark:text-red-300">{{ error }}</p>
            </div>
          </div>
        </div>

        <!-- Success Display -->
        <div v-if="validationResult?.valid" class="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md">
          <div class="flex">
            <CheckCircleIcon class="h-5 w-5 text-green-600 dark:text-green-300 flex-shrink-0" />
            <div class="ml-2">
              <p class="text-sm text-green-800 dark:text-green-300">
                Credentials validated successfully!
                <span v-if="validationResult.account_id">
                  (Account: {{ validationResult.account_id }})
                </span>
              </p>
            </div>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="flex space-x-3 pt-4">
          <button
            type="button"
            @click="validateOnly"
            :disabled="isLoading || !isFormValid"
            class="btn-secondary flex-1"
          >
            <span v-if="isValidating" class="flex items-center justify-center">
              <ArrowPathIcon class="h-4 w-4 animate-spin mr-2" />
              Validating...
            </span>
            <span v-else>Validate Only</span>
          </button>
          <button
            type="submit"
            :disabled="isLoading || !isFormValid"
            class="btn-primary flex-1"
          >
            <span v-if="isLoading && !isValidating" class="flex items-center justify-center">
              <ArrowPathIcon class="h-4 w-4 animate-spin mr-2" />
              Setting...
            </span>
            <span v-else>Set Credentials</span>
          </button>
        </div>

        <!-- Clear Credentials Button -->
        <div v-if="awsStore.hasValidCredentials" class="pt-4 border-t border-gray-200 dark:border-gray-700">
          <button
            type="button"
            @click="clearCredentials"
            :disabled="isLoading"
            class="w-full btn-secondary text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 border-red-300 dark:border-red-600 hover:border-red-400 dark:hover:border-red-500"
          >
            <span v-if="isLoading && !isValidating" class="flex items-center justify-center">
              <ArrowPathIcon class="h-4 w-4 animate-spin mr-2" />
              Clearing...
            </span>
            <span v-else>Clear Credentials</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { 
  CheckCircleIcon, 
  XCircleIcon, 
  ExclamationTriangleIcon,
  ArrowPathIcon
} from '@heroicons/vue/24/outline'
import { useAwsStore } from '@/stores/aws'
import type { AWSCredentialsRequest, AWSCredentialsValidation } from '@/types/api'

const awsStore = useAwsStore()

// Form state
const credentialType = ref<'keys' | 'profile'>('keys')
const form = ref<AWSCredentialsRequest>({
  access_key_id: '',
  secret_access_key: '',
  session_token: '',
  region: 'us-east-1',
  profile: ''
})

// UI state
const isLoading = ref(false)
const isValidating = ref(false)
const error = ref<string | null>(null)
const validationResult = ref<AWSCredentialsValidation | null>(null)

// Computed
const isFormValid = computed(() => {
  if (credentialType.value === 'keys') {
    return !!(form.value.access_key_id && form.value.secret_access_key && form.value.region)
  } else {
    return !!(form.value.profile && form.value.region)
  }
})

// Watch credential type changes to clear form
watch(credentialType, (newType) => {
  if (newType === 'keys') {
    form.value.profile = ''
  } else {
    form.value.access_key_id = ''
    form.value.secret_access_key = ''
    form.value.session_token = ''
  }
  error.value = null
  validationResult.value = null
})

// Methods
const validateOnly = async () => {
  if (!isFormValid.value) return

  isValidating.value = true
  error.value = null
  validationResult.value = null

  try {
    const credentials = createCredentialsObject()
    const result = await awsStore.validateCredentials(credentials)
    validationResult.value = result
    
    if (!result.valid) {
      error.value = result.error || 'Invalid credentials'
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to validate credentials'
  } finally {
    isValidating.value = false
  }
}

const handleSubmit = async () => {
  if (!isFormValid.value) return

  isLoading.value = true
  error.value = null
  validationResult.value = null

  try {
    const credentials = createCredentialsObject()
    await awsStore.setCredentials(credentials)
    
    // Show success message
    validationResult.value = { valid: true }
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to set credentials'
  } finally {
    isLoading.value = false
  }
}

const clearCredentials = async () => {
  if (!confirm('Are you sure you want to clear your AWS credentials?')) return

  isLoading.value = true
  error.value = null

  try {
    await awsStore.clearCredentials()
    
    // Reset form
    form.value = {
      access_key_id: '',
      secret_access_key: '',
      session_token: '',
      region: 'us-east-1',
      profile: ''
    }
    validationResult.value = null
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to clear credentials'
  } finally {
    isLoading.value = false
  }
}

const createCredentialsObject = (): AWSCredentialsRequest => {
  if (credentialType.value === 'keys') {
    return {
      access_key_id: form.value.access_key_id,
      secret_access_key: form.value.secret_access_key,
      session_token: form.value.session_token || undefined,
      region: form.value.region,
      profile: undefined
    }
  } else {
    return {
      access_key_id: undefined,
      secret_access_key: undefined,
      session_token: undefined,
      region: form.value.region,
      profile: form.value.profile
    }
  }
}

// Initialize form with current credentials info
onMounted(() => {
  if (awsStore.credentialsInfo) {
    form.value.region = awsStore.credentialsInfo.region
    
    if (awsStore.credentialsInfo.profile) {
      credentialType.value = 'profile'
      form.value.profile = awsStore.credentialsInfo.profile
    } else if (awsStore.credentialsInfo.has_access_key) {
      credentialType.value = 'keys'
      // Don't populate the actual keys for security
    }
  }
})
</script> 