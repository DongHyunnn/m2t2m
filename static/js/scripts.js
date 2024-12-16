// 업로드 버튼 처리
document.getElementById("upload-form").addEventListener("submit", async (event) => {
    event.preventDefault(); // 기본 폼 제출 동작 방지

    const fileInput = document.getElementById("audio-file");
    const formData = new FormData();

    // 파일 유효성 검사
    if (!fileInput.files.length) {
        alert("Please select a WAV file to upload.");
        return;
    }

    formData.append("audio-file", fileInput.files[0]);

    // 서버에 파일 업로드 요청
    const response = await fetch("/upload", {
        method: "POST",
        body: formData,
    });

    if (response.ok) {
        const result = await response.json();
        alert("File uploaded successfully!");

        // 업로드된 파일 재생 URL 설정
        const audioPlayer = document.getElementById("audio-player-row-1");
        const audioSource = document.getElementById("audio-source-row-1");
        audioSource.src = result.file_url;
        audioPlayer.style.display = "block";
        audioPlayer.load();
    } else {
        alert("Failed to upload the file. Please try again.");
    }
});

// 음악 분석 버튼 처리
document.getElementById("music-analysis-button").addEventListener("click", async () => {
    alert("Analyzing uploaded music...");
    
    const response = await fetch("/analyze-music", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({}), // 분석 요청
    });

    if (response.ok) {
        const result = await response.json();
        alert("Music analysis completed!");

        // 생성된 캡션 표시
        const captionDiv = document.getElementById("generated-caption-row-2");
        captionDiv.textContent = result.caption || "No caption generated.";
        captionDiv.style.display = "block";
    } else {
        alert("Failed to analyze music. Please try again.");
    }
});

// Generate Music 버튼 처리
document.getElementById("generate-music-button-row-3").addEventListener("click", async () => {
    const button = document.getElementById("generate-music-button-row-3");
    const textInput = document.getElementById("additional-text").value.trim();

    // 텍스트 입력 유효성 검사
    if (!textInput) {
        alert("Please enter some text for music generation.");
        return;
    }

    // 버튼 비활성화 및 로딩 메시지 표시
    button.disabled = true;
    button.textContent = "Generating...";

    try {
        // 서버에 텍스트 전송
        const response = await fetch("/generate-music", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ text: textInput }),
        });

        if (response.ok) {
            const result = await response.json();
            generatedCaption = result.new_caption; // 생성된 캡션 저장
            alert("Music generation completed!");

            // 생성된 캡션 표시
            const captionDiv = document.getElementById("generated-caption-row-3");
            captionDiv.textContent = generatedCaption || "No caption generated.";  // 캡션을 해당 HTML 요소에 표시
            captionDiv.style.display = "block";  // 표시되도록 설정
        } else {
            alert("Failed to generate music. Please try again.");
        }
    } catch (error) {
        console.error("Error generating music:", error);
        alert("An error occurred while generating music.");
    } finally {
        // 버튼 활성화 및 원래 텍스트로 복원
        button.disabled = false;
        button.textContent = "Generate Music";
    }
});

// 최종 음악 생성 버튼 처리
document.getElementById("generate-music-button-row-4").addEventListener("click", async () => {
    alert("Generating final music...");

    const response = await fetch("/final-music", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({}), // 음악 생성 요청
    });

    if (response.ok) {
        const result = await response.json();
        alert("Final music generated successfully!");

        // 생성된 음악 재생 URL 설정
        const generatedPlayer = document.getElementById("generated-music-player-row-4");
        const generatedSource = document.getElementById("generated-music-source-row-4");
        generatedSource.src = result.file_url;
        generatedPlayer.style.display = "block";
        generatedPlayer.load();
    } else {
        alert("Failed to generate final music. Please try again.");
    }
});
