<template>
  <div class="training-list-container">
    <HeaderNav />
    <div class="main-content">
      <div class="page-header">
        <h2>我的训练日</h2>
        <el-button type="primary" @click="showCreateDialog = true">
          <i class="el-icon-plus"></i> 新建训练日
        </el-button>
      </div>

      <!-- 训练日列表 -->
      <el-card v-if="trainingList.length > 0" class="list-card">
        <el-table :data="trainingList" border stripe>
          <el-table-column prop="training_day_name" label="训练日名称" min-width="300"></el-table-column>
          <el-table-column prop="created_time" label="创建时间" width="200"></el-table-column>
          <el-table-column label="完成进度" width="150">
            <template #default="scope">
              <el-progress :percentage="Math.round((scope.row.finished_project_count / scope.row.project_count) * 100)"></el-progress>
            </template>
          </el-table-column>
          <el-table-column label="整体评分" width="120">
            <template #default="scope">
              <el-tag :type="scope.row.overall_score >= 80 ? 'success' : scope.row.overall_score >= 60 ? 'warning' : 'danger'">
                {{ scope.row.overall_score }}分
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="scope">
              <el-tag :type="scope.row.is_finished ? 'success' : 'warning'">
                {{ scope.row.is_finished ? '已完成' : '进行中' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150">
            <template #default="scope">
              <el-button type="primary" size="small" @click="goToDetail(scope.row.training_day_id)">
                {{ scope.row.is_finished ? '查看报告' : '继续训练' }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-empty v-else description="暂无训练日，点击右上角新建训练日开始训练"></el-empty>

      <!-- 新建训练日弹窗 -->
      <el-dialog v-model="showCreateDialog" title="新建训练日" width="600px">
        <el-form :model="createForm" label-width="100px">
          <el-form-item label="训练日名称" required>
            <el-input v-model="createForm.training_day_name" placeholder="如：20260305-网络布线日常训练"></el-input>
          </el-form-item>
          <el-form-item label="训练项目">
            <el-checkbox-group v-model="selectedProjectIds">
              <el-checkbox v-for="item in presetProjects" :key="item.project_id" :label="item.project_id">
                {{ item.project_name }}
              </el-checkbox>
            </el-checkbox-group>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button type="primary" @click="createTrainingDay" :loading="createLoading">创建</el-button>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import axios from 'axios'
import HeaderNav from '@/components/HeaderNav.vue'

const router = useRouter()
const trainingList = ref([])
const showCreateDialog = ref(false)
const createLoading = ref(false)
const presetProjects = ref([])
const selectedProjectIds = ref([])
const userInfo = ref({ username: '' })

// 创建训练日表单
const createForm = ref({
  training_day_name: '',
  username: ''
})

// 初始化用户信息
const initUserInfo = () => {
  try {
    const userInfoStr = localStorage.getItem('userInfo')
    if (userInfoStr) {
      userInfo.value = JSON.parse(userInfoStr)
      createForm.value.username = userInfo.value.username
    } else {
      router.push('/login')
    }
  } catch (e) {
    ElMessage.warning('用户信息异常，请重新登录')
    router.push('/login')
  }
}

// 获取预设项目
const getPresetProjects = async () => {
  try {
    const res = await axios.get('/api/training/project/preset')
    if (res.data.code === 200) {
      presetProjects.value = res.data.preset_projects
      // 默认全选
      selectedProjectIds.value = presetProjects.value.map(item => item.project_id)
    }
  } catch (err) {
    ElMessage.error('获取预设项目失败')
  }
}

// 获取训练日列表
const getTrainingList = async () => {
  if (!userInfo.value.username) return
  try {
    const res = await axios.post('/api/training/day/list', {
      username: userInfo.value.username
    })
    if (res.data.code === 200) {
      trainingList.value = res.data.list
    }
  } catch (err) {
    ElMessage.error('获取训练日列表失败')
  }
}

// 创建训练日
const createTrainingDay = async () => {
  if (!createForm.value.training_day_name) {
    ElMessage.warning('请输入训练日名称')
    return
  }
  if (selectedProjectIds.value.length === 0) {
    ElMessage.warning('请至少选择一个训练项目')
    return
  }

  createLoading.value = true
  try {
    // 生成自定义项目列表
    const customProjects = presetProjects.value
      .filter(item => selectedProjectIds.value.includes(item.project_id))
      .map((item, idx) => ({
        project_id: item.project_id,
        project_name: item.project_name,
        project_desc: item.project_desc,
        project_order: idx + 1
      }))

    const res = await axios.post('/api/training/day/create', {
      ...createForm.value,
      custom_projects: customProjects
    })

    if (res.data.code === 200) {
      ElMessage.success('训练日创建成功！')
      showCreateDialog.value = false
      getTrainingList()
      // 跳转到详情页
      router.push(`/training/day-detail/${res.data.training_day_data.training_day_id}`)
    }
  } catch (err) {
    ElMessage.error('创建训练日失败')
  } finally {
    createLoading.value = false
  }
}

// 跳转到详情页
const goToDetail = (id) => {
  router.push(`/training/day-detail/${id}`)
}

onMounted(() => {
  initUserInfo()
  getPresetProjects()
  getTrainingList()
})
</script>

<style scoped>
.training-list-container {
  min-height: 100vh;
  background: #f5f7fa;
}
.main-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 30px 20px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.page-header h2 {
  margin: 0;
  color: #1e293b;
}
.list-card {
  border-radius: 12px;
}
</style>