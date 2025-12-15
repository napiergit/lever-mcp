// Shared email templates for all email tools
export interface EmailTemplate {
    subject: string;
    body: string;
}

export const EMAIL_TEMPLATES: Record<string, EmailTemplate> = {
    birthday: {
        subject: "🎉 Happy Birthday! Let's Celebrate! 🎂",
        body: `
<html>
<body style="font-family: Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px;">
    <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 20px; padding: 40px; box-shadow: 0 10px 40px rgba(0,0,0,0.2);">
        <h1 style="color: #667eea; text-align: center; font-size: 48px; margin-bottom: 20px;">🎉 Happy Birthday! 🎉</h1>
        <p style="font-size: 18px; color: #333; line-height: 1.6;">
            Wishing you a day filled with happiness, laughter, and all your favorite things! 
            May this year bring you endless joy and amazing adventures! 🎂🎈
        </p>
        <div style="text-align: center; margin: 30px 0;">
            <div style="font-size: 60px;">🎁 🎊 🎈 🎂 🎉</div>
        </div>
        <p style="font-size: 16px; color: #666; text-align: center;">
            Have an absolutely wonderful day!
        </p>
    </div>
</body>
</html>
`
    },
    pirate: {
        subject: "⚓ Ahoy Matey! A Message from the Seven Seas! 🏴‍☠️",
        body: `
<html>
<body style="font-family: 'Courier New', monospace; background: #1a1a2e; padding: 40px;">
    <div style="max-width: 600px; margin: 0 auto; background: #16213e; border: 3px solid #e94560; border-radius: 15px; padding: 40px; box-shadow: 0 10px 40px rgba(233, 69, 96, 0.3);">
        <h1 style="color: #e94560; text-align: center; font-size: 42px; margin-bottom: 20px;">⚓ Ahoy Matey! ⚓</h1>
        <p style="font-size: 18px; color: #f1f1f1; line-height: 1.6;">
            Arrr! This be a message from the high seas! 🏴‍☠️
        </p>
        <p style="font-size: 16px; color: #ddd; line-height: 1.6; font-style: italic;">
            May yer sails be full and yer treasure chest overflow with doubloons! 
            Keep a weather eye on the horizon, and may the winds be ever in yer favor!
        </p>
        <div style="text-align: center; margin: 30px 0; font-size: 50px;">
            🏴‍☠️ ⚓ 🗺️ 💰 ⚔️
        </div>
        <p style="font-size: 14px; color: #999; text-align: center;">
            Fair winds and following seas!<br>
            - Captain of the Digital Seas
        </p>
    </div>
</body>
</html>
`
    },
    space: {
        subject: "🚀 Greetings from the Cosmos! ✨",
        body: `
<html>
<body style="font-family: 'Arial', sans-serif; background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%); padding: 40px;">
    <div style="max-width: 600px; margin: 0 auto; background: rgba(255,255,255,0.05); border: 2px solid #4facfe; border-radius: 20px; padding: 40px; box-shadow: 0 0 40px rgba(79, 172, 254, 0.3);">
        <h1 style="color: #4facfe; text-align: center; font-size: 42px; margin-bottom: 20px; text-shadow: 0 0 20px rgba(79, 172, 254, 0.5);">🚀 Cosmic Greetings! 🌟</h1>
        <p style="font-size: 18px; color: #e0e0e0; line-height: 1.6;">
            Transmitting message from the outer reaches of the galaxy! 
            May your journey through the cosmos be filled with wonder and discovery! 🌌
        </p>
        <div style="text-align: center; margin: 30px 0; font-size: 50px;">
            🌍 🛸 ⭐ 🌙 🪐
        </div>
        <p style="font-size: 14px; color: #999; text-align: center;">
            To infinity and beyond!<br>
            - Your Intergalactic Friend
        </p>
    </div>
</body>
</html>
`
    },
    medieval: {
        subject: "⚔️ A Royal Decree from the Kingdom! 👑",
        body: `
<html>
<body style="font-family: 'Georgia', serif; background: linear-gradient(135deg, #2c1810 0%, #4a2c1a 100%); padding: 40px;">
    <div style="max-width: 600px; margin: 0 auto; background: #f4e4c1; border: 5px solid #8b6914; border-radius: 10px; padding: 40px; box-shadow: 0 10px 40px rgba(0,0,0,0.5);">
        <h1 style="color: #8b6914; text-align: center; font-size: 42px; margin-bottom: 20px; font-family: 'Georgia', serif;">⚔️ Royal Decree ⚔️</h1>
        <p style="font-size: 18px; color: #2c1810; line-height: 1.6; font-style: italic;">
            Hear ye, hear ye! By order of the realm, we extend our warmest greetings! 
            May your days be filled with honor, valor, and prosperity! 👑
        </p>
        <div style="text-align: center; margin: 30px 0; font-size: 50px;">
            🏰 ⚔️ 🛡️ 👑 🐉
        </div>
        <p style="font-size: 14px; color: #666; text-align: center;">
            Long live the kingdom!<br>
            - The Royal Court
        </p>
    </div>
</body>
</html>
`
    },
    superhero: {
        subject: "💥 Superhero Alert! You're Amazing! 🦸",
        body: `
<html>
<body style="font-family: 'Impact', 'Arial Black', sans-serif; background: linear-gradient(135deg, #ff0844 0%, #ffb199 100%); padding: 40px;">
    <div style="max-width: 600px; margin: 0 auto; background: #fff; border: 5px solid #ff0844; border-radius: 15px; padding: 40px; box-shadow: 0 10px 40px rgba(255, 8, 68, 0.3);">
        <h1 style="color: #ff0844; text-align: center; font-size: 48px; margin-bottom: 20px; text-transform: uppercase;">💥 POW! 💥</h1>
        <p style="font-size: 18px; color: #333; line-height: 1.6; font-weight: bold;">
            Calling all heroes! You have the power to make today AMAZING! 
            Keep being the superhero you are! 🦸‍♀️🦸‍♂️
        </p>
        <div style="text-align: center; margin: 30px 0; font-size: 50px;">
            ⚡ 💪 🦸 🌟 💥
        </div>
        <p style="font-size: 14px; color: #666; text-align: center;">
            With great power comes great awesomeness!<br>
            - Your Superhero Squad
        </p>
    </div>
</body>
</html>
`
    },
    tropical: {
        subject: "🌴 Aloha! Tropical Vibes Coming Your Way! 🌺",
        body: `
<html>
<body style="font-family: 'Arial', sans-serif; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 40px;">
    <div style="max-width: 600px; margin: 0 auto; background: #fff; border-radius: 25px; padding: 40px; box-shadow: 0 10px 40px rgba(245, 87, 108, 0.3);">
        <h1 style="color: #f5576c; text-align: center; font-size: 48px; margin-bottom: 20px;">🌴 Aloha! 🌺</h1>
        <p style="font-size: 18px; color: #333; line-height: 1.6;">
            Sending you tropical vibes and sunny smiles! 
            May your day be as bright and beautiful as a beach sunset! 🌅
        </p>
        <div style="text-align: center; margin: 30px 0; font-size: 50px;">
            🌴 🌺 🥥 🏖️ 🌊
        </div>
        <p style="font-size: 14px; color: #666; text-align: center;">
            Stay breezy!<br>
            - Your Island Friends
        </p>
    </div>
</body>
</html>
`
    }
};
