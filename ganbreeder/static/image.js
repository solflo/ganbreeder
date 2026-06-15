post_json('/image_children', { key }).then(data => {
    const content = document.querySelector('.image_container.content')
    const thumbs = content.getElementsByClassName('imglink')
    document.getElementById('loading_container').style.display = 'none'
    for (let i = 0; i < data.length; i++) {
        const childKey = data[i].key
        thumbs[i].href = '/i?k=' + childKey
        thumbs[i].firstElementChild.src = root + childKey + '.jpeg'
    }
}).catch(err => {
    console.log({ err })
})

const star = document.getElementById('star')
const starimg = star.querySelector('img')

star.onclick = (event) => {
    event.stopPropagation()
    if (localStorage.getItem(key)) {
        starimg.src = '/image/star_empty.png'
        localStorage.removeItem(key)
        return
    }
    localStorage.setItem(key, new Date().getTime())
    starimg.src = '/image/star_full.png'
    post('/star', {key}).then(() => {
        console.log('Star success')
    })
}

if (localStorage.getItem(key)) {
    starimg.src = '/image/star_full.png'
} else {
    starimg.src = '/image/star_empty.png'
}
