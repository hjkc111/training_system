<template>
  <div class="plan-page">
    <HeaderNav />
    <div class="plan-content">
      <el-card shadow="never" class="plan-card">
        <template #header>
          <div class="card-header">
            <i class="el-icon-s-data"></i>
            <span>光电项目训练计划生成</span>
          </div>
        </template>

        <!-- 第一步：选择训练日 -->
        <div class="plan-step">
          <h3 class="step-title">1. 选择已完成的光电训练日</h3>
          <el-form :model="form" label-width="120px" class="plan-form">
            <el-form-item label="训练日名称">
              <el-select
                v-model="form.trainingDayId"
                placeholder="请选择训练日"
                clearable
                @change="handleTrainingDayChange"
                style="width: 400px;"
              >
                <el-option
                  v-for="day in trainingDayList"
                  :key="day.training_day_id"
                  :label="day.training_day_name"
                  :value="day.training_day_id"
                >
                  <template #label>
                    <div class="option-label">
                      <span>{{ day.training_day_name }}</span>
                      <span class="option-time">{{ day.created_time }}</span>
                    </div>
                  </template>
                </el-option>
              </el-select>
            </el-form-item>
          </el-form>
        </div>

        <!-- 第二步：展示选中训练日的核心分析 -->
        <div v-if="selectedTrainingDay" class="plan-step">
          <h3 class="step-title">2. 训练日核心分析结果</h3>
          <el-collapse class="analysis-collapse">
            <el-collapse-item title="整体评分与完成情况">
              <el-descriptions :column="3" border size="small">
                <el-descriptions-item label="整体评分">
                  {{ selectedTrainingDay.overall_score || 0 }}分
                </el-descriptions-item>
                <el-descriptions-item label="完成项目数">
                  {{ finishedProjectCount }} / {{ totalProjectCount }}
                </el-descriptions-item>
                <el-descriptions-item label="平均项目得分">
                  {{ averageProjectScore.toFixed(1) }}分
                </el-descriptions-item>
              </el-descriptions>
            </el-collapse-item>
            <el-collapse-item title="薄弱项目分析">
              <div v-if="weakProjects.length > 0" class="weak-project-list">
                <div v-for="project in weakProjects" :key="project.project_id" class="weak-project-item">
                  <el-tag type="danger">{{ project.project_name }}</el-tag>
                  <p><strong>得分：</strong>{{ project.analysis_result?.project_score || 0 }}分</p>
                  <p><strong>主要问题：</strong>{{ project.analysis_result?.action_norm_analysis || '暂无分析' }}</p>
                  <p><strong>扣分项：</strong>
                    <span v-for="(deduction, idx) in project.analysis_result?.deduction_items || []" :key="idx">
                      {{ deduction.reason }}(-{{ deduction.deduction_score }}分)
                    </span>
                  </p>
                </div>
              </div>
              <p v-else class="no-weak-tip">暂无明显薄弱项目，整体表现良好</p>
            </el-collapse-item>
          </el-collapse>
        </div>

        <!-- 第三步：生成训练计划 -->
        <div class="plan-step">
          <h3 class="step-title">3. 生成个性化训练计划</h3>
          <el-button
            type="primary"
            size="large"
            @click="generateTrainingPlan"
            :loading="generating"
            :disabled="!form.trainingDayId"
          >
            <i class="el-icon-magic"></i> 生成详细训练计划
          </el-button>
        </div>

        <!-- 第四步：展示生成的训练计划 -->
        <div v-if="trainingPlan" class="plan-step">
          <h3 class="step-title">4. 光电项目个性化训练计划</h3>
          <div class="plan-content-wrapper">
            <!-- 计划头部信息 -->
            <div class="plan-header">
              <h4>{{ trainingPlan.plan_title }}</h4>
              <p>{{ trainingPlan.plan_desc }}</p>
              <el-tag type="info">{{ trainingPlan.plan_days }}天训练周期</el-tag>
              <el-tag type="success">核心目标：{{ trainingPlan.core_goal }}</el-tag>
            </div>

            <!-- 分天训练计划（核心） -->
            <div class="daily-plan-list">
              <div v-for="(dayPlan, idx) in trainingPlan.daily_plans" :key="idx" class="daily-plan-item">
                <div class="daily-header">
                  <span class="day-num">第{{ idx + 1 }}天</span>
                  <span class="day-theme">{{ dayPlan.theme }}</span>
                  <span class="day-goal">{{ dayPlan.daily_goal }}</span>
                </div>

                <!-- 当天训练项目 -->
                <div class="project-plan-list">
                  <div v-for="(projectPlan, pIdx) in dayPlan.project_plans" :key="pIdx" class="project-plan-item">
                    <h5>{{ pIdx + 1 }}. {{ projectPlan.project_name }}</h5>
                    <div class="plan-detail">
                      <div class="detail-item">
                        <label>训练内容：</label>
                        <p>{{ projectPlan.training_content }}</p>
                      </div>
                      <div class="detail-item">
                        <label>训练方法：</label>
                        <ul>
                          <li v-for="(method, mIdx) in projectPlan.training_methods" :key="mIdx">{{ method }}</li>
                        </ul>
                      </div>
                      <div class="detail-item">
                        <label>验收标准：</label>
                        <p>{{ projectPlan.acceptance_criteria }}</p>
                      </div>
                      <div class="detail-item">
                        <label>注意事项：</label>
                        <p>{{ projectPlan.notes }}</p>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- 当天总结与次日提示 -->
                <div class="daily-summary">
                  <label>当日总结：</label>
                  <p>{{ dayPlan.daily_summary }}</p>
                  <label v-if="idx < trainingPlan.plan_days - 1">次日预习：</label>
                  <p v-if="idx < trainingPlan.plan_days - 1">{{ dayPlan.next_day_tips }}</p>
                </div>
              </div>
            </div>

            <!-- 计划总结 -->
            <div class="plan-summary">
              <h4>训练计划总结</h4>
              <p>{{ trainingPlan.plan_summary }}</p>
              <el-alert
                title="执行建议"
                type="warning"
                :closable="false"
                style="margin-top: 10px;"
              >
                {{ trainingPlan.execution_suggestion }}
              </el-alert>
            </div>

            <!-- 导出计划按钮 -->
            <div class="plan-action">
              <el-button type="success" @click="exportTrainingPlan">
                <i class="el-icon-download"></i> 导出训练计划
              </el-button>
            </div>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import axios from 'axios'
import HeaderNav from '@/components/HeaderNav.vue'

// ===================== 基础变量 =====================
const router = useRouter()
// 从本地存储获取用户信息（需确保登录后存储）
const userInfo = ref(JSON.parse(localStorage.getItem('userInfo') || '{}'))

// ===================== 表单/状态变量 =====================
// 选择训练日的表单
const form = ref({
  trainingDayId: '' // 选中的训练日ID
})
// 光电训练日列表（后端返回）
const trainingDayList = ref([])
// 选中的训练日详情（后端返回）
const selectedTrainingDay = ref(null)
// 生成计划加载状态
const generating = ref(false)
// 最终生成的训练计划（后端返回）
const trainingPlan = ref(null)

// ===================== 计算属性（基于选中训练日） =====================
// 总项目数
const totalProjectCount = computed(() => {
  return selectedTrainingDay.value?.project_list?.length || 0
})
// 已完成（有分析结果）的项目数
const finishedProjectCount = computed(() => {
  return selectedTrainingDay.value?.project_list?.filter(p => p.is_analyzed).length || 0
})
// 平均项目得分
const averageProjectScore = computed(() => {
  const projects = selectedTrainingDay.value?.project_list || []
  if (projects.length === 0) return 0
  const totalScore = projects.reduce((sum, p) => {
    return sum + (p.analysis_result?.project_score || 0)
  }, 0)
  return totalScore / projects.length
})
// 薄弱项目（得分<80分）
const weakProjects = computed(() => {
  const projects = selectedTrainingDay.value?.project_list || []
  return projects.filter(p => p.is_analyzed && (p.analysis_result?.project_score || 0) < 80)
})

// ===================== 接口调用逻辑（全标注） =====================
/**
 * 接口1：获取光电训练日列表
 * 后端接口路径：POST /api/photoelectric/training/day/list
 * 请求参数：{ username: string }
 * 响应格式：
 * {
 *   code: 200,
 *   list: [
 *     {
 *       training_day_id: string,    // 训练日ID
 *       training_day_name: string,  // 训练日名称
 *       created_time: string,       // 创建时间（格式：YYYY-MM-DD）
 *       overall_score: number       // 整体评分（仅返回有评分的训练日）
 *     }
 *   ]
 * }
 */
const getPhotoelectricTrainingDays = async () => {
  if (!userInfo.value.username) {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }
  try {
    const res = await axios.post('/api/photoelectric/training/day/list', {
      username: userInfo.value.username
    })
    if (res.data.code === 200) {
      // 只展示已完成的训练日（有整体评分的）
      trainingDayList.value = res.data.list.filter(day => day.overall_score)
    }
  } catch (err) {
    ElMessage.error('获取训练日列表失败：' + (err.response?.data?.detail || err.message))
  }
}

/**
 * 接口2：获取训练日详情
 * 后端接口路径：POST /api/photoelectric/training/day/detail
 * 请求参数：{ training_day_id: string, username: string }
 * 响应格式：
 * {
 *   code: 200,
 *   detail: {
 *     training_day_id: string,
 *     training_day_name: string,
 *     overall_score: number,
 *     created_time: string,
 *     project_list: [
 *       {
 *         project_id: string,
 *         project_name: string,
 *         is_analyzed: boolean,     // 是否有AI分析结果
 *         analysis_result: {        // AI分析结果
 *           project_score: number,  // 项目得分
 *           action_norm_analysis: string, // 操作规范性分析
 *           deduction_items: [      // 扣分项
 *             { reason: string, deduction_score: number }
 *           ]
 *         }
 *       }
 *     ]
 *   }
 * }
 */
const handleTrainingDayChange = async (trainingDayId) => {
  if (!trainingDayId) {
    selectedTrainingDay.value = null
    trainingPlan.value = null
    return
  }
  try {
    const res = await axios.post('/api/photoelectric/training/day/detail', {
      training_day_id: trainingDayId,
      username: userInfo.value.username
    })
    if (res.data.code === 200) {
      selectedTrainingDay.value = res.data.detail
      trainingPlan.value = null // 清空原有计划
    }
  } catch (err) {
    ElMessage.error('获取训练日详情失败：' + (err.response?.data?.detail || err.message))
  }
}

/**
 * 接口3：生成光电训练计划
 * 后端接口路径：POST /api/ai/generate-photoelectric-plan
 * 请求参数：
 * {
 *   username: string,
 *   training_day_id: string,
 *   training_day_data: object  // 选中的训练日完整数据（selectedTrainingDay.value）
 * }
 * 响应格式：
 * {
 *   code: 200,
 *   plan: {
 *     plan_title: string,        // 计划标题
 *     plan_desc: string,         // 计划描述
 *     plan_days: number,         // 训练天数
 *     core_goal: string,         // 核心目标
 *     daily_plans: [             // 分天计划
 *       {
 *         theme: string,         // 当日训练主题
 *         daily_goal: string,    // 当日目标
 *         project_plans: [       // 当日项目计划
 *           {
 *             project_name: string,       // 项目名称
 *             training_content: string,   // 训练内容
 *             training_methods: string[], // 训练方法
 *             acceptance_criteria: string,// 验收标准
 *             notes: string               // 注意事项
 *           }
 *         ],
 *         daily_summary: string,  // 当日总结
 *         next_day_tips: string   // 次日预习提示（最后一天无）
 *       }
 *     ],
 *     plan_summary: string,      // 计划总结
 *     execution_suggestion: string // 执行建议
 *   }
 * }
 */
const generateTrainingPlan = async () => {
  if (!selectedTrainingDay.value) return
  generating.value = true
  try {
    // 调用后端生成计划接口
    const res = await axios.post('/api/ai/generate-photoelectric-plan', {
      username: userInfo.value.username,
      training_day_id: form.value.trainingDayId,
      training_day_data: selectedTrainingDay.value // 传给后端用于生成计划的原始数据
    })
    if (res.data.code === 200) {
      trainingPlan.value = res.data.plan
      ElMessage.success('光电项目训练计划生成成功！')
    } else {
      ElMessage.error('生成失败：' + res.data.detail)
    }
  } catch (err) {
    ElMessage.error('生成训练计划失败：' + (err.response?.data?.detail || err.message))
  } finally {
    generating.value = false
  }
}

/**
 * 接口4：导出训练计划
 * 后端接口路径：POST /api/ai/export-photoelectric-plan
 * 请求参数：{ plan_id: string / plan_data: object, username: string }
 * 响应：返回文件流（Excel/PDF）
 */
const exportTrainingPlan = async () => {
  try {
    // 发起导出请求（设置响应类型为blob）
    const res = await axios.post(
      '/api/ai/export-photoelectric-plan',
      {
        username: userInfo.value.username,
        plan_data: trainingPlan.value // 直接传计划数据，或传plan_id（后端需支持）
      },
      {
        responseType: 'blob', // 关键：接收文件流
        headers: { 'Content-Type': 'application/json' }
      }
    )
    // 处理文件下载
    const blob = new Blob([res.data], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
    const downloadUrl = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = downloadUrl
    a.download = `${trainingPlan.value.plan_title}.docx` // 文件名
    a.click()
    window.URL.revokeObjectURL(downloadUrl) // 释放URL
    ElMessage.success('训练计划导出成功！')
  } catch (err) {
    ElMessage.error('导出训练计划失败：' + (err.response?.data?.detail || err.message))
  }
}

// ===================== 页面初始化 =====================
onMounted(() => {
  // 页面加载时获取训练日列表
  getPhotoelectricTrainingDays()
})
</script>

<style scoped>
.plan-page {
  min-height: 100vh;
  background: #f5f7fa;
}
.plan-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 30px 20px;
}
.plan-card {
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
  margin-bottom: 20px;
}
.card-header i {
  color: #3b82f6;
}
.plan-step {
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid #f0f0f0;
}
.plan-step:last-child {
  border-bottom: none;
}
.step-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.step-title::before {
  content: '';
  display: inline-block;
  width: 4px;
  height: 16px;
  background: #3b82f6;
  border-radius: 2px;
}
.plan-form {
  margin-left: 10px;
}
.option-label {
  display: flex;
  flex-direction: column;
}
.option-time {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 2px;
}
.analysis-collapse {
  margin-left: 10px;
}
.weak-project-list {
  margin-top: 10px;
}
.weak-project-item {
  padding: 10px;
  background: #fef2f2;
  border-radius: 8px;
  margin-bottom: 10px;
}
.no-weak-tip {
  color: #64748b;
  padding: 10px;
  text-align: center;
}
.plan-content-wrapper {
  margin-left: 10px;
}
.plan-header {
  padding: 15px;
  background: #f8fafc;
  border-radius: 8px;
  margin-bottom: 20px;
}
.plan-header h4 {
  margin: 0 0 8px 0;
  color: #1e293b;
  font-size: 16px;
  font-weight: 600;
}
.plan-header p {
  margin: 0 0 10px 0;
  color: #64748b;
}
.daily-plan-list {
  margin-bottom: 20px;
}
.daily-plan-item {
  padding: 15px;
  background: #f8fafc;
  border-radius: 8px;
  margin-bottom: 15px;
}
.daily-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #e2e8f0;
}
.day-num {
  font-weight: 700;
  color: #3b82f6;
  font-size: 16px;
  background: #eff6ff;
  padding: 2px 8px;
  border-radius: 4px;
}
.day-theme {
  font-weight: 600;
  color: #1e293b;
}
.day-goal {
  color: #64748b;
  font-size: 14px;
  flex: 1;
  margin-left: 10px;
}
.project-plan-list {
  margin-left: 10px;
}
.project-plan-item {
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #e2e8f0;
}
.project-plan-item:last-child {
  border-bottom: none;
}
.project-plan-item h5 {
  margin: 0 0 10px 0;
  color: #1e293b;
  font-size: 15px;
}
.plan-detail {
  margin-left: 10px;
}
.detail-item {
  margin-bottom: 8px;
}
.detail-item label {
  font-weight: 600;
  color: #334155;
  display: inline-block;
  width: 80px;
}
.detail-item p {
  display: inline;
  color: #475569;
  margin: 0;
}
.detail-item ul {
  display: inline-block;
  margin: 0;
  padding-left: 20px;
  color: #475569;
}
.daily-summary {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #e2e8f0;
  margin-left: 10px;
}
.daily-summary label {
  font-weight: 600;
  color: #334155;
  display: inline-block;
  width: 80px;
}
.daily-summary p {
  display: inline;
  color: #475569;
  margin: 0;
}
.plan-summary {
  padding: 15px;
  background: #f8fafc;
  border-radius: 8px;
  margin-top: 20px;
}
.plan-summary h4 {
  margin: 0 0 10px 0;
  color: #1e293b;
  font-size: 15px;
  font-weight: 600;
}
.plan-summary p {
  margin: 0 0 10px 0;
  color: #475569;
}
.plan-action {
  margin-top: 20px;
  text-align: right;
}
</style>