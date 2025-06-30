var swiper = new Swiper(".swiper", {
  loop: true,
  autoplay: {
    delay: 4000,
    disableOnInteraction: false
  },
  navigation: {
    nextEl: ".swiper-button-next",
    prevEl: ".swiper-button-prev"
  },
  pagination: {
    el: ".swiper-pagination",
    clickable: true
  },
  speed: 600,
  slidesPerGroup: 1,

  breakpoints: {
    0: { slidesPerView: 1, spaceBetween: 5},
    700: { slidesPerView: 2, spaceBetween: 15},
    800: { slidesPerView: 2, spaceBetween: 15},
    855: { slidesPerView: 2, spaceBetween: 30},
    900: { slidesPerView: 2, spaceBetween: 20},
    1000: { slidesPerView: 3, spaceBetween: 15},
    1350: { slidesPerView: 4, spaceBetween: 12},
    1400: { slidesPerView: 4, spaceBetween: 15},
    1500: { slidesPerView: 4, spaceBetween: 20}
  }
});


document.addEventListener('DOMContentLoaded', function () {
  new Swiper('.swiper-container', {
    loop: true,
    spaceBetween: 20,
    slidesPerView: 'auto',
    centeredSlides: true,
    navigation: {
      nextEl: '.swiper-button-next',
      prevEl: '.swiper-button-prev',
    },
    pagination: {
      el: '.swiper-pagination',
      clickable: true,
    },
    breakpoints: {
      320: { slidesPerView: 3, spaceBetween: 10},
      640: { slidesPerView: 3, spaceBetween: 10},
      700: { slidesPerView: 3},
      1000: { slidesPerView: 4},
      1200: { slidesPerView: 5},
      1300: { slidesPerView: 5},
      1400: { slidesPerView: 5},
      1500: { slidesPerView: 5, spaceBetween: 15},
      1700: { slidesPerView: 5, spaceBetween: 35},
    },
    autoplay: {
      delay: 2000,  
      disableOnInteraction: false,
    },
    speed: 600,  
  });
});