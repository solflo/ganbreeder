const source_url = document.getElementById('source_url')
const source_image = document.getElementById('source_image')
const width_input = document.getElementById('width')
const height_input = document.getElementById('height')
const variation = document.getElementById('variation')
const seamless = document.getElementById('seamless')
const render = document.getElementById('render')
const loading = document.getElementById('loading_container')
const result = document.getElementById('result')
const result_img = result.querySelector('img')
const permalink = result.querySelector('.permalink')

const get_key = (url) => new URLSearchParams(new URL(url, location.origin).search).get('k')
const snap = (input) => Math.max(base, Math.round(Number(input.value) / step) * step)

function preview() {
    const key = get_key(source_url.value)
    source_image.style.visibility = 'hidden'
    if (!key) return
    source_image.src = root + key + '.jpeg'
    source_image.onload = () => source_image.style.visibility = 'visible'
}

if (prefill_key) source_url.value = '/i?k=' + prefill_key
preview()
source_url.oninput = preview
source_url.onpaste = preview

document.querySelectorAll('.presets button').forEach(button => button.addEventListener('click', () => {
    width_input.value = button.dataset.width
    height_input.value = button.dataset.height
}))

render.addEventListener('click', () => {
    const key = get_key(source_url.value)
    if (!key) return alert('Paste a ganbreeder image url first.')

    const width = width_input.value = snap(width_input)
    const height = height_input.value = snap(height_input)
    const amount = variation.value = Math.min(1, Math.max(0, Number(variation.value) || 0))
    if (width * height > max_pixels) return alert(`Too big, keep width x height under ${max_pixels} pixels.`)

    loading.style.display = ''
    result.style.display = 'none'
    render.disabled = true
    const payload = { key, width, height, tile: seamless.checked, variation: amount }
    post_json('/expand_image', payload).then(data => {
        const src = root + data.key + '.jpeg'
        loading.style.display = 'none'
        result_img.src = src
        permalink.href = '/i?k=' + data.key
        result.style.display = ''
        render.disabled = false
    }).catch(err => {
        console.log(err)
        loading.style.display = 'none'
        render.disabled = false
        alert('There was an error :\'(')
    })
})
