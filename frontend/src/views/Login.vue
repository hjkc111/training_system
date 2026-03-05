<template>
  <div class="login-container">
    <el-card class="login-card" shadow="hover">
      <!-- 标题改为训练管理平台 -->
      <h2 class="login-title">训练管理平台</h2>
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        @submit="handleLogin"
        label-width="80px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            clearable
            border="normal"
            round
          ></el-input>
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            clearable
            show-password
            border="normal"
            round
          ></el-input>
        </el-form-item>
        <el-form-item label="身份" prop="role">
          <el-select 
            v-model="loginForm.role" 
            placeholder="请选择身份"
            border="normal"
            round
          >
            <el-option label="选手" value="player"></el-option>
            <el-option label="教练" value="coach"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            class="login-btn"
            :loading="loading"
            native-type="submit"
            round
          >
            {{ loading ? '登录中...' : '登录' }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const loginFormRef = ref(null)
const loading = ref(false)

// 登录表单数据
const loginForm = reactive({
  username: '',
  password: '',
  role: 'player'
})

// 表单验证规则
const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择身份', trigger: 'change' }
  ]
}

// 登录处理函数
const handleLogin = async (e) => {
  // 1. 阻止表单默认提交（核心修复点）
  e.preventDefault()

  try {
    // 2. 先验证表单，验证通过后再发送请求
    await loginFormRef.value.validate()
    loading.value = true

    // 3. 发送登录请求
    const res = await axios.post('/api/auth/login', {
      username: loginForm.username,
      password: loginForm.password,
      role: loginForm.role
    })

    if (res.data.code === 200) {
      // 4. 登录成功：保存用户信息并跳转（避免页面刷新重复触发）
      ElMessage.success('登录成功！')
      localStorage.setItem('userInfo', JSON.stringify(res.data.user_info))
      // 改为跳转到首页
      router.push('/home') 
    } else {
      ElMessage.error(res.data.message || '登录失败，请检查用户名密码！')
    }
  } catch (err) {
    // 5. 处理错误：区分表单验证错误和请求错误
    if (err.name === 'FormValidationError') {
      // 表单验证失败，不触发登录请求
      return
    }
    ElMessage.error('登录失败，请检查用户名密码或网络连接！')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* 纯白色背景 */
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #ffffff; /* 纯空白背景 */
  padding: 20px;
}

/* 登录卡片 - 圆角、轻微阴影 */
.login-card {
  width: 400px;
  padding: 30px;
  border-radius: 12px; /* 圆滑边框 */
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05); /* 轻微阴影更柔和 */
  border: 1px solid #f0f0f0;
}

/* 标题样式 */
.login-title {
  text-align: center;
  margin-bottom: 30px;
  color: #303133;
  font-size: 20px;
  font-weight: 600;
}

/* 登录按钮 - 蓝色主色，hover变深 */
.login-btn {
  width: 100%;
  height: 44px;
  border-radius: 8px; /* 按钮圆角 */
  background-color: #1989fa !important; /* 主蓝色 */
  border: none !important;
  transition: background-color 0.2s ease;
}
/* hover时颜色加深 */
.login-btn:hover {
  background-color: #0f7ae5 !important;
}

/* 统一表单元素圆角（element plus的round属性已生效，这里增强兼容性） */
:deep(.el-input--round .el-input__inner),
:deep(.el-select--round .el-select__wrapper),
:deep(.el-button--round) {
  border-radius: 8px !important;
}

/* 表单标签文字样式优化 */
:deep(.el-form-item__label) {
  color: #606266;
  font-weight: 500;
}

/* 响应式适配 */
@media (max-width: 450px) {
  .login-card {
    width: 100%;
  }
}
</style>