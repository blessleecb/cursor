const quotes = [
    { text: "삶이 있는 한 희망은 있다.", author: "키케로" },
    { text: "산다는것 그것은 치열한 전투이다.", author: "로망로랑" },
    { text: "하루에 3시간을 걸으면 7년 후에 지구를 한바퀴 돌 수 있다.", author: "사무엘존슨" },
    { text: "언제나 현재에 집중할수 있다면 행복할것이다.", author: "파울로 코엘료" },
    { text: "진정으로 웃으려면 고통을 참아야하며 , 나아가 고통을 즐길 줄 알아야 해.", author: "찰리 채플린" },
    { text: "직업에서 행복을 찾아라. 아니면 행복이 무엇인지 절대 모를 것이다.", author: "엘버트 허버드" },
    { text: "신은 용기있는자를 결코 버리지 않는다.", author: "켄러" },
    { text: "피할수 없으면 즐겨라.", author: "로버트 엘리엇" },
    { text: "단순하게 살아라. 현대인은 쓸데없는 절차와 일 때문에 얼마나 복잡한 삶을 살아가는가?", author: "이다사히" },
    { text: "먼저 자신을 용서하라. 그래야 타인도 용서할 수 있다.", author: "에픽테토스" }
];

const quoteText = document.getElementById('quote-text');
const quoteAuthor = document.getElementById('quote-author');
const prevBtn = document.getElementById('prev-btn');
const nextBtn = document.getElementById('next-btn');
const randomBtn = document.getElementById('random-btn');

let currentIndex = 0;
let history = [];

function displayQuote(index) {
    quoteText.textContent = `"${quotes[index].text}"`;
    quoteAuthor.textContent = `- ${quotes[index].author} -`;
}

function showNext() {
    if (history.length > 0 && history[history.length - 1] === currentIndex) {
        // We don't want to duplicate the current state if we are just moving sequentially
    } else {
        history.push(currentIndex);
    }
    
    currentIndex = (currentIndex + 1) % quotes.length;
    displayQuote(currentIndex);
}

function showPrev() {
    if (history.length > 0) {
        currentIndex = history.pop();
    } else {
        currentIndex = (currentIndex - 1 + quotes.length) % quotes.length;
    }
    displayQuote(currentIndex);
}

function showRandom() {
    history.push(currentIndex);
    let randomIndex;
    do {
        randomIndex = Math.floor(Math.random() * quotes.length);
    } while (randomIndex === currentIndex && quotes.length > 1);
    
    currentIndex = randomIndex;
    displayQuote(currentIndex);
}

// Event Listeners
prevBtn.addEventListener('click', showPrev);
nextBtn.addEventListener('click', showNext);
randomBtn.addEventListener('click', showRandom);

// Initial display
displayQuote(currentIndex);