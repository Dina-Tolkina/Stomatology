document.addEventListener("DOMContentLoaded", function () {
    const doctorSelect = document.getElementById("id_doctor");
    const serviceSelect = document.getElementById("id_service");
    const dateInput = document.getElementById("id_date");
    const timeInput = document.getElementById("id_time");
    const otherServiceInput = document.getElementById("id_other_service");
    const otherServiceLabel = document.querySelector('label[for="id_other_service"]');

    doctorSelect.addEventListener("change", function () {
        handleDoctorSelection(doctorSelect.value);
    });

    serviceSelect.addEventListener("change", function () {
        handleServiceSelection(serviceSelect);
    });

    timeInput.addEventListener("click", function () {
        const doctorId = doctorSelect.value;
        const date = dateInput.value;
        
        if (doctorId && date) {
            updateTimes(doctorId, date); 
        }
    });

    function handleDoctorSelection(doctorId) {
        if (doctorId) {
            serviceSelect.disabled = false;
            serviceSelect.innerHTML = `<option value="">Выберите услугу</option>`; 
            dateInput.disabled = true;
            timeInput.disabled = true;
            dateInput.value = "";
            timeInput.value = "";

            fetch(`/get_services_dates/${doctorId}/`)
                .then(response => response.json())
                .then(data => {
                    data.services.forEach(service => {
                        serviceSelect.innerHTML += `<option value="${service.id}">${service.name}</option>`;
                    });
                });

            dateInput.disabled = true;
            timeInput.disabled = true;
        } else {
            serviceSelect.disabled = true;
            serviceSelect.innerHTML = `<option value="">Сначала выберите врача</option>`;
            dateInput.disabled = true;
            timeInput.disabled = true;
        }
    }

    function handleServiceSelection(serviceSelect) {
        if (serviceSelect.options[serviceSelect.selectedIndex].text === "Другая услуга") {
            otherServiceInput.style.display = "block";
            otherServiceLabel.style.display = "block";
            otherServiceInput.setAttribute("required", "true");
        } else {
            otherServiceInput.style.display = "none";
            otherServiceLabel.style.display = "none";
            otherServiceInput.value = "";
            otherServiceInput.removeAttribute("required");
        }
        dateInput.disabled = false;
        dateInput.placeholder = ""; 
        dateInput.type = "date";
    }

    dateInput.addEventListener("change", function () {
        const doctorId = doctorSelect.value;
        const date = dateInput.value;

        if (date) {
            timeInput.placeholder = "Выберите время";  
            updateTimes(doctorId, date);
            timeInput.disabled = false;  
        } else {
            timeInput.disabled = true;  
        }
    });

    function updateTimes(doctorId, date) {
        if (!doctorId || !date) return;
    
        fetch(`/get_available_times/${doctorId}/${date}/`)
            .then(response => response.json())
            .then(data => {
                let timeContainer = document.getElementById("time-container");
                let timeInput = document.getElementById("id_time");
    
                if (!timeContainer) {
                    timeContainer = document.createElement("div");
                    timeContainer.id = "time-container";
                    document.body.appendChild(timeContainer);
                }
    
                timeContainer.innerHTML = ""; 
    
                let now = new Date();
                let selectedDate = new Date(date);
                let currentHours = now.getHours();
                let currentMinutes = now.getMinutes();
    
                let hasAvailableTimes = false;  
    
                data.times.forEach(time => {
                    let [startTime, endTime] = time.split("-"); 
                    let [startHours, startMinutes] = startTime.split(":").map(Number);
                    let [endHours, endMinutes] = endTime.split(":").map(Number);
    
                    if (selectedDate.toDateString() === now.toDateString()) {
                        if (startHours < currentHours || 
                            (startHours === currentHours && startMinutes <= currentMinutes)) {
                            return;  
                        }
                    }
    
                    let button = document.createElement("button");
                    button.type = "button";
                    button.classList.add("time-button");
                    button.textContent = time;
    
                    button.onclick = function () {
                        const isSelected = button.classList.contains("selected");
                        document.querySelectorAll(".time-button").forEach(btn => btn.classList.remove("selected"));
    
                        if (!isSelected) {
                            button.classList.add("selected");
                            timeInput.value = time;
                            timeContainer.style.display = "none";
                        } else {
                            timeContainer.style.display = timeContainer.style.display === "none" ? "grid" : "none";
                        }
                    };
    
                    timeContainer.appendChild(button);
                    hasAvailableTimes = true;  
                });
    
                if (!hasAvailableTimes) {
                    let noTimesMessage = document.createElement("p");
                    noTimesMessage.textContent = "К сожалению, на эту дату больше нет доступных записей. Попробуйте выбрать другую дату.";
                    timeContainer.appendChild(noTimesMessage);
                    timeContainer.classList.add("no-grid");
                } else {
                    timeContainer.classList.remove("no-grid"); 
                }
    
                timeContainer.style.display = "grid";
                let rect = timeInput.getBoundingClientRect();
                timeContainer.style.top = rect.bottom + window.scrollY + "px";
                timeContainer.style.left = rect.left + "px";
            });
    }
    
});

// Инициализация Flatpickr для выбора даты
document.addEventListener("DOMContentLoaded", function () {
    flatpickr("#id_date", {
        enableTime: false, 
        dateFormat: "Y-m-d",
        minDate: "today", 
        locale: "ru", 
        disableMobile: true
    });
});

// Маска для номера телефона
$(document).ready(function() {
    $('#id_phone_number').mask('+7(000)000-00-00');
});

