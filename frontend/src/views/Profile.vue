<template>
  <div class="profile-page">
    <HeaderNav />
    <div class="profile-content">
      <el-card shadow="never" class="profile-card">
        <template #header>
          <div class="card-header">
            <i class="el-icon-user"></i>
            <span>个人中心</span>
          </div>
        </template>
        <el-descriptions title="个人信息" border class="profile-desc">
          <el-descriptions-item label="用户名">{{ userInfo.username || '未获取' }}</el-descriptions-item>
          <el-descriptions-item label="身份">{{ userInfo.role === 'player' ? '选手' : '教练' }}</el-descriptions-item>
          <el-descriptions-item label="登录时间">{{ loginTime || '未知' }}</el-descriptions-item>
        </el-descriptions>
        <!-- 后续可添加：修改密码、个人资料编辑等 -->
        <el-button type="primary" class="logout-btn" @click="logout">退出登录</el-button>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import HeaderNav from '@/components/HeaderNav.vue'

const router = useRouter()
const userInfo = ref({})
const loginTime = ref('')

// 初始化用户信息
onMounted(() => {
  try {
    const userInfoStr = localStorage.getItem('userInfo')
    if (userInfoStr) {
      userInfo.value = JSON.parse(userInfoStr)
    }
    // 模拟登录时间（后续可存localStorage）
    loginTime.value = new Date().toLocaleString()
  } catch (e) {
    ElMessage.warning('用户信息异常')
  }
})

// 退出登录
const logout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    localStorage.clear()
    router.push('/login')
    ElMessage.success('退出登录成功')
  } catch (e) {
    ElMessage.info('已取消退出')
  }
}
</script>

<style scoped>
.profile-page {
  min-height: 100vh;
  background: #f5f7fa;
}
.profile-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 30px 20px;
}
.profile-card {
  background: white;
  border-radius: 12px;
  padding: 30px;
}
.card-header {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
  display: flex;
  align-items: center;
  gap: 8px;
}
.card-header i {
  color: #3b82f6;
}
.profile-desc {
  margin: 20px 0;
}
.logout-btn {
  margin-top: 20px;
}
</style>