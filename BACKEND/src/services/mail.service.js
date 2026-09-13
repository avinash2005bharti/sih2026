const { BrevoClient } = require("@getbrevo/brevo");

const brevo = new BrevoClient({
    apiKey: process.env.BREVO_API_KEY
});

async function sendTemporaryPassword(email, tempPassword) {

    const htmlContent = `
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif;">

            <h2>Password Reset</h2>

            <p>Your password has been reset successfully.</p>

            <p>Your temporary password is:</p>

            <div style="
                background:#f4f4f4;
                padding:15px;
                font-size:20px;
                font-weight:bold;
                letter-spacing:2px;
                display:inline-block;
            ">
                ${tempPassword}
            </div>

            <p>
                Please log in using this temporary password
                and change your password immediately.
            </p>

            <p>
                If you did not request this password reset,
                please contact the administrator.
            </p>

            <br>

            <p>
                Regards,<br>
                <strong>Sovereign AI Workbench</strong>
            </p>

        </body>
        </html>
    `;

    try {
        const response = await brevo.transactionalEmails.sendTransacEmail({
            subject: "Your Temporary Password",
            htmlContent,
            sender: {
                name: "Sovereign AI Workbench",
                email: process.env.BREVO_SENDER_EMAIL
            },
            to: [{ email: email }]
        });

        console.log("📧 Email sent successfully:", response);

        return response;

    } catch (error) {
        console.error(
            "❌ Brevo email error:",
            error.response?.body || error.message
        );

        throw error;
    }
}

module.exports = {
    sendTemporaryPassword
};