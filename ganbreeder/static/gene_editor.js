const dropdown = document.getElementById('label_dropdown')
const search = document.getElementById('label_search')
const rows = document.getElementById('gene_rows')
const template = document.getElementById('gene_row_template')
const generate = document.getElementById('generate')
const loading = document.getElementById('loading_container')
const result = document.getElementById('result')
const result_link = result.querySelector('.imglink')
const result_img = result_link.firstElementChild
const options = [...dropdown.children]

const used = (index) => !!rows.querySelector(`.gene_row[data-index="${index}"]`)

function refresh() {
    let total = 0
    rows.querySelectorAll('.gene_slider').forEach(s => total += Number(s.value))
    rows.querySelectorAll('.gene_row').forEach(row => {
        const w = Number(row.querySelector('.gene_slider').value)
        row.querySelector('.gene_percent').textContent = total > 0 ? `${(w / total * 100).toFixed(1)}%` : '—'
    })
    generate.disabled = total <= 0
}

function add_row(index, name, weight) {
    const row = template.content.firstElementChild.cloneNode(true)
    row.dataset.index = index
    row.querySelector('.gene_name').textContent = name
    const slider = row.querySelector('.gene_slider')
    const number = row.querySelector('.gene_weight')
    slider.value = weight
    number.value = Math.round(weight * 100)
    slider.addEventListener('input', () => {
        number.value = Math.round(slider.value * 100)
        refresh()
    })
    number.addEventListener('input', () => {
        slider.value = Math.min(Math.max(Number(number.value) || 0, 0), 100) / 100
        refresh()
    })
    row.querySelector('.gene_remove').addEventListener('click', () => {
        row.remove()
        refresh()
    })
    rows.appendChild(row)
    refresh()
}

function filter() {
    const q = search.value.trim().toLowerCase()
    options.forEach(li => {
        li.hidden = used(li.dataset.index) || !li.textContent.toLowerCase().includes(q)
    })
}

options.forEach(li => li.addEventListener('mousedown', event => {
    event.preventDefault()
    add_row(li.dataset.index, li.textContent, 0.5)
    search.value = ''
    dropdown.style.display = 'none'
}))


search.addEventListener('click', () => {
    filter()
    dropdown.style.display = ''
})
// search.addEventListener('input', filter)
search.addEventListener('input', () => {
    filter()
    dropdown.style.display = ''
})
search.addEventListener('blur', () => setTimeout(() => (dropdown.style.display = 'none'), 120))

generate.addEventListener('click', () => {
    const label = {}
    rows.querySelectorAll('.gene_row').forEach(row => {
        label[row.dataset.index] = Number(row.querySelector('.gene_slider').value)
    })
    const payload = key ? { label, key } : { label }
    loading.style.display = ''
    result.style.display = 'none'
    generate.disabled = true
    post_json('/generate_image', payload).then(data => {
        loading.style.display = 'none'
        result_link.href = '/i?k=' + data.key
        result_img.src = root + data.key + '.jpeg'
        result.style.display = ''
        generate.disabled = false
    }).catch(err => {
        console.log(err)
        loading.style.display = 'none'
        generate.disabled = false
        alert('There was an error :\'(')
    })
})

for (const [index, weight] of Object.entries(initial_genes)) {
    const li = dropdown.querySelector(`li[data-index="${index}"]`)
    add_row(index, li.textContent, Number(weight))
}
