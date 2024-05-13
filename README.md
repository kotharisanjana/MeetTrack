# MeetTrack - Smart Meeting Assistant

#### Motivation
In today's rapidly evolving digital landscape, the role of smart assistants in boosting productivity cannot be overstated. With an increasing number of teams spread across geographical boundaries, virtual collaboration has become a cornerstone of modern work. Consequently, it has become imperative to leverage technology to enhance user experience and make remote collaboration more seamless.

In the realm of smart meeting assistants, two major issues persist: first, the fragmentation of valuable smart features across different tools and video-conferencing platforms. Second, the exorbitant costs associated with acquiring them, particularly for users with limited budgets. Moreover, existing tools may not identify individual speakers by voice and not capture the visual content shared during meetings, leading to incomplete meeting records. Additionally, keeping track of previous or current discussions can become tedious, especially in long and recurring meetings. By providing real-time interaction capabilities, users can effortlessly navigate through meeting content using natural language. Lastly, MeetTrack being a browser extension is compatible with any web-based video conferencing platform, eliminating restrictions around choice of platform.

MeetTrack aims to overcome aforementioned challenges and make advanced smart functionalities accessible to a wider audience for more productive and engaging meetings.

<br/>

#### About 
MeetTrack is a Google Chrome browser extension that is designed to integrate with web-based video conferencing platforms. MeetTrack includes the following key components:
* Voice-based speaker identification.
* Automatic speech  recognition.
* AI generated meeting notes that capture different elements like: 
  * Meeting summary
  * Action items/ to-do list for participants
  * Key decisions and takeaways
  * Summaries of verbal messages of appreciation and recognition.
* Relevant and contextual-aware visual content from presentations shared during meetings along with descriptions which is beneficial when sharing notes with stakeholders and cross-functional teams.
* A user interaction engine that allows participants to ask questions in real-time about the discussion from the current meeting and the previous meetings, if any.

<br/>

#### System Process Flow
![Screenshot from 2024-05-13 10-31-54](https://github.com/kotharisanjana/MeetTrack/assets/60322201/a53fe58f-0ee4-4b41-80d8-66a2bb270d95)
![Screenshot from 2024-05-13 10-32-04](https://github.com/kotharisanjana/MeetTrack/assets/60322201/f7f944bc-ea95-42a2-97a9-8332b04b7be3)

<br/>

#### System Architecture
![Screenshot from 2024-05-13 10-28-22](https://github.com/kotharisanjana/MeetTrack/assets/60322201/a7dff18a-05bd-4b75-b27f-5af553218737)

<br/>

#### Browser Extension
![Screenshot from 2024-05-13 10-33-08](https://github.com/kotharisanjana/MeetTrack/assets/60322201/963ac43d-5182-4b59-bff9-7cf7e4d1aafb)

<br/>

#### Tools and Technologies 
1. Flask (Python)
2. JavaScript
3. Amazon Web Services (EC2, S3, RDS, ECR)
4. Databases - PostgreSQL, Qdrant, Redis
5. ML Models - OpenAI GPT, Google Gemini Vision, OpenAI Whisper, SBert, PyAnnote/Speaker-Diarization
6. Frameworks - LangChain, LlamaIndex

<br/>

#### Usage
1. Clone the repository
2. Navigate to chrome://extensions on Google Chrome
3. Upload extension-frontend folder
4. Extension is visible in the extensions tab and is ready to use

Walk into your meetings and experience them like never before!

<br/>

#### Demo
https://github.com/kotharisanjana/MeetTrack/assets/60322201/55bd275c-131e-40ed-a3f8-c5a011002b0b



