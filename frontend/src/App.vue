<script setup>
import { reactive, ref } from 'vue'

const API = import.meta.env.VITE_API_URL || 'http://localhost:5000'
const UFS = [
  'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS',
  'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC',
  'SP', 'SE', 'TO',
]
const TAMANHO_PAGINA = 20

const filtros = reactive({ nome: '', similar: false, cargo: '', uf: '', orgao: '' })
const resultado = ref({ data: [], page: 1, total: 0, total_pages: 0 })
const erro = ref('')
const carregando = ref(false)
const buscou = ref(false)

function montarQuery(pagina) {
  const params = new URLSearchParams({ page: pagina, page_size: TAMANHO_PAGINA })
  let temTexto = false
  for (const campo of ['nome', 'cargo', 'orgao']) {
    const valor = filtros[campo].trim()
    if (valor) {
      params.set(campo, valor)
      temTexto = true
    }
  }
  const uf = filtros.uf.trim()
  if (uf) params.set('uf', uf)
  if (filtros.similar && temTexto) params.set('similar', 'true')
  return params.toString()
}

async function buscar(pagina = 1) {
  carregando.value = true
  erro.value = ''
  try {
    const resposta = await fetch(`${API}/api/servidores?${montarQuery(pagina)}`)
    const corpo = await resposta.json()
    if (!resposta.ok) {
      erro.value = corpo.error || 'Erro na consulta'
      return
    }
    resultado.value = corpo
    buscou.value = true
  } catch {
    erro.value = 'Nao foi possivel conectar ao servidor'
  } finally {
    carregando.value = false
  }
}

function limpar() {
  Object.assign(filtros, { nome: '', similar: false, cargo: '', uf: '', orgao: '' })
  resultado.value = { data: [], page: 1, total: 0, total_pages: 0 }
  erro.value = ''
  buscou.value = false
}
</script>

<template>
  <main>
    <header>
      <h1>Consulta de Servidores Federais</h1>
      <p>Dados de amostra de servidores ativos e aposentados.</p>
    </header>

    <form class="filtros" @submit.prevent="buscar(1)">
      <label>
        Nome
        <input v-model="filtros.nome" type="text" maxlength="200" placeholder="Ex.: ANA LIMA" />
      </label>
      <label>
        Cargo
        <input v-model="filtros.cargo" type="text" maxlength="200" />
      </label>
      <label>
        UF
        <select v-model="filtros.uf">
          <option value="">Todas</option>
          <option v-for="uf in UFS" :key="uf" :value="uf">{{ uf }}</option>
        </select>
      </label>
      <label>
        Orgao
        <input v-model="filtros.orgao" type="text" maxlength="200" />
      </label>
      <label class="similar">
        <input v-model="filtros.similar" type="checkbox" />
        Busca similar (use % como coringa)
      </label>
      <div class="acoes">
        <button type="submit" :disabled="carregando">Buscar</button>
        <button type="button" class="secundario" @click="limpar">Limpar</button>
      </div>
    </form>

    <p v-if="erro" class="erro">{{ erro }}</p>

    <section v-if="resultado.data.length">
      <p class="resumo">{{ resultado.total }} registro(s) encontrado(s)</p>
      <div class="tabela">
        <table>
          <thead>
            <tr>
              <th>Nome</th>
              <th>Cargo</th>
              <th>Orgao</th>
              <th>UF</th>
              <th>Situacao</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="linha in resultado.data" :key="linha.id">
              <td>{{ linha.nome }}</td>
              <td>{{ linha.cargo }}</td>
              <td>{{ linha.orgao }}</td>
              <td>{{ linha.uf }}</td>
              <td>{{ linha.situacao }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <nav class="paginacao">
        <button :disabled="carregando || resultado.page <= 1" @click="buscar(resultado.page - 1)">
          Anterior
        </button>
        <span>Pagina {{ resultado.page }} de {{ resultado.total_pages }}</span>
        <button
          :disabled="carregando || resultado.page >= resultado.total_pages"
          @click="buscar(resultado.page + 1)"
        >
          Proxima
        </button>
      </nav>
    </section>

    <p v-else-if="buscou && !erro" class="vazio">Nenhum servidor encontrado.</p>
  </main>
</template>

<style>
:root {
  --cor-fundo: #f4f6f8;
  --cor-texto: #1f2933;
  --cor-primaria: #1d4e89;
  --cor-primaria-clara: #e6eef8;
  --cor-borda: #d5dde5;
  --cor-erro: #b42318;
  --raio: 6px;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  background: var(--cor-fundo);
  color: var(--cor-texto);
  font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
}

main {
  max-width: 1100px;
  margin: 0 auto;
  padding: 24px 16px 48px;
}

header h1 {
  margin: 0 0 4px;
  color: var(--cor-primaria);
  font-size: 1.6rem;
}

header p {
  margin: 0 0 24px;
  color: #52606d;
}

.filtros {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  padding: 20px;
  background: #fff;
  border: 1px solid var(--cor-borda);
  border-radius: var(--raio);
}

.filtros label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 0.9rem;
  font-weight: 600;
}

.filtros label.similar {
  flex-direction: row;
  align-items: center;
  font-weight: 400;
  align-self: end;
}

input,
select,
button {
  font: inherit;
}

input[type='text'],
select {
  padding: 8px 10px;
  border: 1px solid var(--cor-borda);
  border-radius: var(--raio);
  background: #fff;
}

.acoes {
  display: flex;
  gap: 10px;
  align-items: end;
}

button {
  padding: 8px 16px;
  border: 1px solid var(--cor-primaria);
  border-radius: var(--raio);
  background: var(--cor-primaria);
  color: #fff;
  cursor: pointer;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

button.secundario {
  background: #fff;
  color: var(--cor-primaria);
}

.erro {
  margin: 16px 0 0;
  color: var(--cor-erro);
  font-weight: 600;
}

.vazio {
  margin-top: 24px;
  color: #52606d;
}

.resumo {
  margin: 24px 0 8px;
  color: #52606d;
}

.tabela {
  overflow-x: auto;
  background: #fff;
  border: 1px solid var(--cor-borda);
  border-radius: var(--raio);
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.92rem;
}

th,
td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid var(--cor-borda);
}

th {
  background: var(--cor-primaria-clara);
  color: var(--cor-primaria);
}

.paginacao {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-top: 16px;
}
</style>
