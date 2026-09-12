import {
  useEffect,
  useState,
} from "react";

import {
  getProfile,
  updateProfile,
} from "../services/userService.js";

import "../styles/profile-page.css";


function ProfilePage() {
  const [profile, setProfile] =
    useState(null);

  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    phone: "",
  });

  const [loading, setLoading] =
    useState(true);

  const [saving, setSaving] =
    useState(false);

  const [error, setError] =
    useState("");

  const [success, setSuccess] =
    useState("");


  async function loadProfile() {
    try {
      setLoading(true);
      setError("");

      const data =
        await getProfile();

      setProfile(data);

      setForm({
        first_name:
          data.first_name || "",
        last_name:
          data.last_name || "",
        phone:
          data.phone || "",
      });
    } catch (requestError) {
      console.error(
        "Failed to load profile:",
        requestError,
      );

      setError(
        "Unable to load your profile. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  }


  useEffect(() => {
    loadProfile();
  }, []);


  function handleChange(event) {
    const {
      name,
      value,
    } = event.target;

    setForm((current) => ({
      ...current,
      [name]: value,
    }));

    setSuccess("");
    setError("");
  }


  async function handleSubmit(event) {
    event.preventDefault();

    try {
      setSaving(true);
      setError("");
      setSuccess("");

      const updated =
        await updateProfile(form);

      setProfile(updated);

      setForm({
        first_name:
          updated.first_name || "",
        last_name:
          updated.last_name || "",
        phone:
          updated.phone || "",
      });

      setSuccess(
        "Profile updated successfully.",
      );
    } catch (requestError) {
      console.error(
        "Failed to update profile:",
        requestError,
      );

      const responseData =
        requestError?.response?.data;

      const firstError =
        responseData?.phone?.[0] ||
        responseData?.first_name?.[0] ||
        responseData?.last_name?.[0];

      setError(
        firstError ||
          "Unable to update your profile. Please try again.",
      );
    } finally {
      setSaving(false);
    }
  }


  function getRoleLabel() {
    if (!profile) {
      return "—";
    }

    return (
      profile.role_display ||
      profile.role ||
      "—"
    );
  }


  if (loading) {
    return (
      <section className="profile-page">
        <div className="profile-loading">
          Loading profile...
        </div>
      </section>
    );
  }


  return (
    <section className="profile-page">
      <header className="profile-header">
        <div>
          <p className="profile-eyebrow">
            ACCOUNT
          </p>

          <h1>
            Your profile
          </h1>

          <p>
            View your CivicResolve account
            information and update your
            contact details.
          </p>
        </div>
      </header>


      {error && (
        <div
          className="profile-error"
          role="alert"
        >
          {error}
        </div>
      )}


      {success && (
        <div
          className="profile-success"
          role="status"
        >
          {success}
        </div>
      )}


      <div className="profile-grid">
        <section className="profile-card">
          <div className="profile-card-header">
            <div>
              <p className="profile-card-eyebrow">
                ACCOUNT INFORMATION
              </p>

              <h2>
                Identity
              </h2>
            </div>
          </div>


          <div className="profile-information">
            <div className="profile-information-row">
              <span>
                Email
              </span>

              <strong>
                {profile?.email ||
                  "—"}
              </strong>
            </div>


            <div className="profile-information-row">
              <span>
                Role
              </span>

              <strong>
                {getRoleLabel()}
              </strong>
            </div>


            {profile?.role ===
              "OFFICER" && (
              <div className="profile-information-row">
                <span>
                  Department
                </span>

                <strong>
                  {profile.department_name ||
                    "Not assigned"}
                </strong>
              </div>
            )}
          </div>
        </section>


        <section className="profile-card">
          <div className="profile-card-header">
            <div>
              <p className="profile-card-eyebrow">
                CONTACT DETAILS
              </p>

              <h2>
                Personal information
              </h2>
            </div>
          </div>


          <form
            className="profile-form"
            onSubmit={
              handleSubmit
            }
          >
            <div className="profile-form-row">
              <div className="profile-field">
                <label htmlFor="first_name">
                  First name
                </label>

                <input
                  id="first_name"
                  name="first_name"
                  type="text"
                  value={
                    form.first_name
                  }
                  onChange={
                    handleChange
                  }
                  autoComplete="given-name"
                  disabled={saving}
                />
              </div>


              <div className="profile-field">
                <label htmlFor="last_name">
                  Last name
                </label>

                <input
                  id="last_name"
                  name="last_name"
                  type="text"
                  value={
                    form.last_name
                  }
                  onChange={
                    handleChange
                  }
                  autoComplete="family-name"
                  disabled={saving}
                />
              </div>
            </div>


            <div className="profile-field">
              <label htmlFor="email">
                Email
              </label>

              <input
                id="email"
                type="email"
                value={
                  profile?.email ||
                  ""
                }
                disabled
              />

              <span className="profile-helper">
                Email cannot be changed
                from your profile.
              </span>
            </div>


            <div className="profile-field">
              <label htmlFor="phone">
                Phone number
              </label>

              <input
                id="phone"
                name="phone"
                type="tel"
                value={
                  form.phone
                }
                onChange={
                  handleChange
                }
                placeholder="Enter your phone number"
                autoComplete="tel"
                disabled={saving}
              />
            </div>


            <button
              type="submit"
              className="profile-save-button"
              disabled={saving}
            >
              {saving
                ? "Saving..."
                : "Save changes"}
            </button>
          </form>
        </section>
      </div>
    </section>
  );
}


export default ProfilePage;