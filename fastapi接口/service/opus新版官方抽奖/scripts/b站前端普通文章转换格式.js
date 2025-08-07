let iframe_doc = $('iframe[src="/article-text/home?"]')[0].contentDocument
let origin_ps = $$(`.ql-editor > p`,iframe_doc)

for (let p of origin_ps){
	us = /https?:\/\/[^\s]+/g.exec(p.innerText)
    if (!us) continue
    for (let u of us)
        {	
        console.log(u)
        p.innerText = p.innerText.replaceAll(u,'')
        let a = document.createElement('a');
        a.href = u;
        a.rel='noopener noreferrer'
        a.target = '_blank'
        a.className='link'
        a.innerText='网页链接'
        p.prepend(a)
    }
}